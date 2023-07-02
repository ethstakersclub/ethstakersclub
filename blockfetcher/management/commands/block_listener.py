from django.core.management.base import BaseCommand
from web3 import Web3
from blockfetcher.tasks import load_epoch_task, load_epoch, get_deposits_task, load_validators, update_validators_task, handle_new_block, load_block_task, make_balance_snapshot_task, load_epoch_rewards_task, fetch_mev_rewards_task, epoch_aggregate_missed_attestations_and_average_mev_reward_task
import asyncio
import json
import requests
from websockets import connect
from ethstakersclub.settings import DEPOSIT_CONTRACT_DEPLOYMENT_BLOCK, EXECUTION_WS_API_ENDPOINT, BEACON_API_ENDPOINT, SLOTS_PER_EPOCH, EXECUTION_HTTP_API_ENDPOINT,\
      w3, MERGE_SLOT, EPOCH_REWARDS_HISTORY_DISTANCE, SECONDS_PER_SLOT, GENESIS_TIMESTAMP, MAX_SLOTS_PER_DAY
import requests
from blockfetcher.models import Main, Block, Validator, Withdrawal, AttestationCommittee, Epoch, ValidatorBalance, MissedAttestation, SyncCommittee
from web3.beacon import Beacon
import decimal
from itertools import islice
from threading import Thread
from concurrent.futures import ThreadPoolExecutor, wait
from threading import Lock
import concurrent.futures
from datetime import datetime
from django.utils import timezone
import time
from django.db import transaction
from ethstakersclub.celery import app as celery_app
import json
from django.db.models import F, Q, Func, Min, Sum, Count
from django.db.models.functions import Lag
from django.db import connection
from django.core.cache import cache
from blockfetcher.management.commands.get_pending_celery_tasks import get_scheduled_tasks_count
from blockfetcher.util import print_status
import sseclient


count = 0
beacon = Beacon(BEACON_API_ENDPOINT)


def send_request_post(what, data):
    url = BEACON_API_ENDPOINT + what
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }

    return requests.post(url, headers=headers, data=data).json()


def load_current_state(main_row):
    current_state = beacon.get_beacon_state()["data"]

    main_row.finalized_checkpoint_epoch = int(current_state["finalized_checkpoint"]["epoch"])
    main_row.finalized_checkpoint_root = str(current_state["finalized_checkpoint"]["root"])
    main_row.justified_checkpoint_epoch = int(current_state["current_justified_checkpoint"]["epoch"])
    main_row.justified_checkpoint_root = str(current_state["current_justified_checkpoint"]["root"])

    #genesis = beacon.get_genesis()["data"]
    #genesis_timestamp = int(genesis["genesis_time"])
    #main_row.genesis_time = timezone.make_aware(datetime.fromtimestamp(genesis_timestamp), timezone=timezone.utc)

    main_row.save()


def create_sync_committee(finalized_check_epoch):
    sync_check_epoch = finalized_check_epoch + 256
    sync_check_slot = finalized_check_epoch * SLOTS_PER_EPOCH
    sync_period = sync_check_epoch / 256
    sync_committee, created = SyncCommittee.objects.get_or_create(period=sync_period)

    if created or sync_committee.validator_ids == None:
        print_status('info', "set up new sync committee for slot " + str(sync_check_slot) + " epoch " + str(sync_check_epoch))

        url = BEACON_API_ENDPOINT + "/eth/v1/beacon/states/" + str(sync_check_slot) + "/sync_committees?epoch=" + str(sync_check_epoch)
        sync_committee_state = requests.get(url).json()

        before_altair = False
        if "code" in sync_committee_state and sync_committee_state["code"] == 400:
            print(sync_committee_state["message"])
            before_altair = True
        if not before_altair:
            print_status('info', "sync committee after altair, proceeding")

            sync_validators = [int(s) for s in sync_committee_state["data"]["validators"]]
            sync_committee.validator_ids = sync_validators
            sync_committee.save()


def sync_up(main_row, last_slot_processed=0, loop_epoch=0, last_balance_update_time=0, reorg=False):
    print_status('info', 'syncing last_slot_processed=' + str(last_slot_processed) + " loop_epoch=" + str(loop_epoch) + " reorg=" + str(reorg))
    
    url = BEACON_API_ENDPOINT + "/eth/v1/beacon/blocks/head"
    head = requests.get(url).json()
    
    head_slot = int(head["data"]["message"]["slot"])
    head_epoch = int(head_slot / SLOTS_PER_EPOCH)
    head_block = w3.eth.get_block_number()

    cache.set("head_slot", head_slot, timeout=10000)
    cache.set("head_epoch", head_epoch, timeout=10000)
    cache.set("head_block", head_block, timeout=10000)

    print_status('info', f'Head is slot={head_slot} epoch={head_epoch} block={head_block}')

    if last_slot_processed == 0:
        load_current_state(main_row)
        print_status('info', 'Setting up validators')
        validator_task = update_validators_task.delay(head_slot)
        while not validator_task.ready():
            time.sleep(1)

        # recheck the previous 35 block as well to ensure there were no reorgs after shutdown
        last_slot_processed = main_row.last_slot - 35
        if last_slot_processed < 0:
            last_slot_processed = 0

        loop_epoch = int(last_slot_processed / SLOTS_PER_EPOCH)
        if loop_epoch > 0:
            load_epoch(loop_epoch - 1, last_slot_processed)
        load_epoch(loop_epoch, last_slot_processed)
        create_sync_committee(loop_epoch - 256)

        SNAPSHOT_CREATION_EPOCH_DELAY = 6
        MEV_FETCH_DELAY_SLOTS = SLOTS_PER_EPOCH * 2
        initial_run = True
    else:
        SNAPSHOT_CREATION_EPOCH_DELAY = 3
        MEV_FETCH_DELAY_SLOTS = 4

        initial_run = False

    last_balance_snapshot_planned_date = main_row.last_balance_snapshot_planned_date
    last_missed_attestation_aggregation_epoch = main_row.last_missed_attestation_aggregation_epoch
    last_mev_reward_fetch_slot = main_row.last_mev_reward_fetch_slot
    last_staking_deposits_update_block = main_row.last_staking_deposits_update_block

    if last_mev_reward_fetch_slot < MERGE_SLOT - 1:
        last_mev_reward_fetch_slot = MERGE_SLOT - 1
    if last_staking_deposits_update_block < DEPOSIT_CONTRACT_DEPLOYMENT_BLOCK - 1:
        last_staking_deposits_update_block = DEPOSIT_CONTRACT_DEPLOYMENT_BLOCK - 1

    if initial_run:
        print_status('info', 'Started up: filling epochs')

        last_epoch_slot_processed = main_row.last_epoch_slot_processed

        if last_epoch_slot_processed < last_slot_processed:
            last_epoch_slot_processed = last_slot_processed

        epochs_processed = 0
        start_time = time.time()
        loop_epoch_initial = loop_epoch
        for slot in range(last_epoch_slot_processed, (main_row.finalized_checkpoint_epoch * SLOTS_PER_EPOCH)):
            while True:
                try:
                    if int(slot / SLOTS_PER_EPOCH) != loop_epoch_initial:
                        load_epoch_task.delay(int(slot / SLOTS_PER_EPOCH), slot)
                        
                        tasks_count = get_scheduled_tasks_count()
                        print(tasks_count)

                        epochs_processed += 1

                        elapsed_time = time.time() - start_time
                        epochs_per_second = (epochs_processed - tasks_count) / elapsed_time
                        print_status('info', f"Epochs per second: {epochs_per_second}, Epochs processed: {epochs_processed}")

                        main_row.last_epoch_slot_processed = slot - SLOTS_PER_EPOCH
                        main_row.save()

                        loop_epoch_initial = int(slot / SLOTS_PER_EPOCH)

                        if tasks_count > 50:
                            print_status('info', 'task queue filled up, waiting...')
                            time.sleep(2)
                    break

                except KeyboardInterrupt:
                    return
                except Exception as e:
                    print_status('error', e)
                    continue

    for i in range(last_staking_deposits_update_block - 60, head_block + 1, 1000):
        while True:
            try:
                to_block = i+1000
                if(to_block > head_block):
                    to_block = head_block

                get_deposits_task.delay(i, to_block)

                last_staking_deposits_update_block=i

                if i % 20 == 0:
                    main_row.last_staking_deposits_update_block = i
                    main_row.save()

                    print_status('info', f"Staking deposit blocks processed: {i}")

                tasks_count = get_scheduled_tasks_count()
                print(tasks_count)
                
                if tasks_count > 50:
                    print_status('info', 'task queue filled up, waiting...')
                    time.sleep(2)

                break
            except KeyboardInterrupt:
                return
            except Exception as e:
                print_status('error', e)
                continue

    main_row.last_staking_deposits_update_block = i
    main_row.save()

    slots_processed = 0
    start_time = time.time()
    for slot in range(last_slot_processed, head_slot+1):
        while True:
            try:
                if int(slot / SLOTS_PER_EPOCH) != loop_epoch:
                    with transaction.atomic():
                        check_epoch = int(slot / SLOTS_PER_EPOCH)
                        if slot >= main_row.last_epoch_slot_processed:
                            load_epoch(check_epoch, slot)
                        else:
                            if not Epoch.objects.filter(epoch=check_epoch).exists():
                                load_epoch(check_epoch, slot)

                        if not reorg:
                            if not initial_run:
                                load_current_state(main_row)

                                sec_since_last_balance_update = (time.time() - last_balance_update_time)
                                if sec_since_last_balance_update > 200:
                                    last_balance_update_time = time.time()
                                    update_validators_task.delay(slot)

                            if check_epoch > head_epoch - EPOCH_REWARDS_HISTORY_DISTANCE - 2:
                                print_status('info', 'load epoch rewards...')
                                task = load_epoch_rewards_task.delay(check_epoch - 2)

                                if initial_run:
                                    while not task.ready():
                                        time.sleep(1)

                            snapshot_creation_timestamp = GENESIS_TIMESTAMP + (SECONDS_PER_SLOT * (slot - (SLOTS_PER_EPOCH * SNAPSHOT_CREATION_EPOCH_DELAY)))
                            snapshot_creation_date = timezone.make_aware(datetime.fromtimestamp(snapshot_creation_timestamp), timezone=timezone.utc)

                            if last_balance_snapshot_planned_date < snapshot_creation_date.date():
                                print_status('info', "snapshot task started " + str(snapshot_creation_date.date()) + " " + str(
                                    last_balance_snapshot_planned_date))
                                make_balance_snapshot_task.delay(slot, snapshot_creation_timestamp)

                                last_balance_snapshot_planned_date = snapshot_creation_date.date()
                                main_row.last_balance_snapshot_planned_date = last_balance_snapshot_planned_date

                            if main_row.finalized_checkpoint_epoch >= check_epoch - 3:
                                finalized_check_epoch = check_epoch - 3
                                for i in range(last_missed_attestation_aggregation_epoch + 1, finalized_check_epoch + 1):
                                    epoch_aggregate_missed_attestations_and_average_mev_reward_task.delay(i)

                                    last_missed_attestation_aggregation_epoch=i
                                    main_row.last_missed_attestation_aggregation_epoch = last_missed_attestation_aggregation_epoch

                                create_sync_committee(finalized_check_epoch)

                            loop_epoch = int(slot / SLOTS_PER_EPOCH)

                            main_row.last_slot = slot
                            main_row.save()

                load_block_task.delay(slot, loop_epoch)
                tasks_count = get_scheduled_tasks_count()

                if slot % MEV_FETCH_DELAY_SLOTS == 0 and last_mev_reward_fetch_slot < slot - 2:
                    fetch_mev_rewards_task.delay(last_mev_reward_fetch_slot, slot - 2)

                    last_mev_reward_fetch_slot = slot-2
                    main_row.last_mev_reward_fetch_slot = last_mev_reward_fetch_slot
                    main_row.save()

                slots_processed += 1
                if slots_processed % 10 == 0:
                    elapsed_time = time.time() - start_time
                    slots_per_second = (slots_processed - tasks_count) / elapsed_time
                    print_status('info', f"Slots per second: {slots_per_second}, Slots processed: {slots_processed}")
                while tasks_count > 50:
                    print_status('info', f'task queue filled up ({tasks_count}), waiting...')
                    time.sleep(3)
                    tasks_count = get_scheduled_tasks_count()
                break

            except KeyboardInterrupt:
                return
            except Exception as e:
                print_status('error', e)
                continue
    
    return head_slot, loop_epoch, last_balance_update_time


async def get_event():
    async with connect(EXECUTION_WS_API_ENDPOINT) as ws:
        await ws.send(json.dumps({"id": 1, "method": "eth_subscribe", "params": ["newHeads"]}))
        subscription_response = await ws.recv()
        print(subscription_response)
        while True:
            try:
                message = await asyncio.wait_for(ws.recv(), timeout=60)
                handle_new_block.delay(json.loads(message))
                print(json.loads(message))
                pass
            except KeyboardInterrupt:
                break


class Command(BaseCommand):
    help = 'Starts the block listener'

    def handle(self, *args, **options):
        #for i in range(187841, 210206):
        #    epoch_aggregate_missed_attestations_and_average_mev_reward_task.delay(i)
        #return
        main_row, created = Main.objects.get_or_create(id=1, defaults={
            'last_balance_snapshot_planned_date': timezone.make_aware(datetime.fromtimestamp(0), timezone=timezone.utc),
            'finalized_checkpoint_epoch': 0,
            'justified_checkpoint_epoch': 0,
            })
        
        print(main_row)
        last_slot_processed, loop_epoch, last_balance_update_time = sync_up(main_row)

        def with_urllib3(url, headers):
            import urllib3
            http = urllib3.PoolManager()
            return http.request('GET', url, preload_content=False, headers=headers)
        
        url = 'http://127.0.0.1:5052/eth/v1/events?topics=chain_reorg,head'
        headers = {'Accept': 'text/event-stream'}
        response = with_urllib3(url, headers)  # or with_requests(url, headers)
        client = sseclient.SSEClient(response)
        last_balance_update_time = time.time()
        for event in client.events():
            print(event.data)
            event_slot=int(json.loads(event.data)["slot"])
            if str(event.event) == "chain_reorg":
                print("reorg")
                print(event_slot)
                loop_epoch = int((event_slot-1) / SLOTS_PER_EPOCH)
                last_slot_processed, loop_epoch, last_balance_update_time = sync_up(main_row, event_slot, loop_epoch, last_balance_update_time, True)
            else:
                print(time.time() - last_balance_update_time)
                last_slot_processed, loop_epoch, last_balance_update_time = sync_up(main_row, last_slot_processed+1, loop_epoch, last_balance_update_time)
