from django.core.management.base import BaseCommand
from blockfetcher.tasks import load_epoch_task, load_epoch, get_deposits_task, process_validators_task,\
                               load_block_task, make_balance_snapshot_task, load_epoch_rewards_task, \
                               fetch_mev_rewards_task, epoch_aggregate_missed_attestations_and_average_mev_reward_task
import json
import requests
from ethstakersclub.settings import DEPOSIT_CONTRACT_DEPLOYMENT_BLOCK, BEACON_API_ENDPOINT, SLOTS_PER_EPOCH,\
                                    w3, MERGE_SLOT, EPOCH_REWARDS_HISTORY_DISTANCE_SYNC, SECONDS_PER_SLOT, GENESIS_TIMESTAMP, \
                                    SNAPSHOT_CREATION_EPOCH_DELAY_SYNC, MAX_TASK_QUEUE, ALTAIR_EPOCH, BEACON_API_ENDPOINT_OPTIONAL_GZIP
import requests
from blockfetcher.models import Main, Epoch, SyncCommittee
from datetime import datetime
from django.utils import timezone
import time
from django.db import transaction
import json
from django.core.cache import cache
from blockfetcher.management.commands.test_get_pending_celery_tasks import get_scheduled_tasks_count
from blockfetcher.util import print_status
import sseclient
from blockfetcher.beacon_api import BeaconAPI


count = 0
beacon = BeaconAPI(BEACON_API_ENDPOINT_OPTIONAL_GZIP)


def send_request_post(what, data):
    url = BEACON_API_ENDPOINT + what
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }

    return requests.post(url, headers=headers, data=data).json()


def load_current_state(main_row):
    current_state = beacon.get_finality_checkpoints("head")["data"]

    main_row.finalized_checkpoint_epoch = int(current_state["finalized"]["epoch"])
    main_row.finalized_checkpoint_root = str(current_state["finalized"]["root"])
    main_row.justified_checkpoint_epoch = int(current_state["current_justified"]["epoch"])
    main_row.justified_checkpoint_root = str(current_state["current_justified"]["root"])

    main_row.save()


def create_sync_committee(finalized_check_epoch):
    sync_check_epoch = finalized_check_epoch + 256
    sync_check_slot = finalized_check_epoch * SLOTS_PER_EPOCH
    if sync_check_slot < ALTAIR_EPOCH * SLOTS_PER_EPOCH:
        sync_check_slot = ALTAIR_EPOCH * SLOTS_PER_EPOCH
    sync_period = sync_check_epoch / 256
    sync_committee, created = SyncCommittee.objects.get_or_create(period=sync_period)

    if finalized_check_epoch > (ALTAIR_EPOCH - 3000):
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


def wait_for_task_queue_to_clear():
    tasks_count = get_scheduled_tasks_count()
    while tasks_count > MAX_TASK_QUEUE:
            print_status('info', f'task queue filled up ({tasks_count}), waiting...')
            time.sleep(1)
            tasks_count = get_scheduled_tasks_count()
    
    return tasks_count


def setup_epochs(main_row, last_slot_processed, loop_epoch):
    last_epoch_slot_processed = main_row.last_epoch_slot_processed

    if last_epoch_slot_processed < last_slot_processed:
        last_epoch_slot_processed = last_slot_processed

    epochs_processed = 0
    start_time = time.time()
    for slot in range(last_epoch_slot_processed, (main_row.finalized_checkpoint_epoch * SLOTS_PER_EPOCH)):
        while True:
            try:
                if int(slot / SLOTS_PER_EPOCH) != loop_epoch:
                    tasks_count = wait_for_task_queue_to_clear()

                    load_epoch_task.delay(int(slot / SLOTS_PER_EPOCH), slot)

                    epochs_processed += 1

                    elapsed_time = time.time() - start_time
                    epochs_per_second = (epochs_processed - tasks_count) / elapsed_time
                    print_status('info', f"Epochs per second: {epochs_per_second}, Epochs processed: {epochs_processed}")

                    if loop_epoch % 10 == 0:
                        main_row.last_epoch_slot_processed = slot - SLOTS_PER_EPOCH
                        main_row.save()

                    loop_epoch = int(slot / SLOTS_PER_EPOCH)
                break
            except KeyboardInterrupt:
                return
            except Exception as e:
                print_status('error', e)
                continue


def setup_staking_deposits(main_row, head_block):
    last_staking_deposits_update_block = main_row.last_staking_deposits_update_block

    if last_staking_deposits_update_block < DEPOSIT_CONTRACT_DEPLOYMENT_BLOCK - 1:
        last_staking_deposits_update_block = DEPOSIT_CONTRACT_DEPLOYMENT_BLOCK - 1

    for i in range(last_staking_deposits_update_block - 60, head_block + 1, 1000):
        while True:
            try:
                wait_for_task_queue_to_clear()

                to_block = i+1000
                if(to_block > head_block):
                    to_block = head_block

                get_deposits_task.delay(i, to_block)

                last_staking_deposits_update_block=i

                if i % 20 == 0:
                    main_row.last_staking_deposits_update_block = i
                    main_row.save()

                    print_status('info', f"Staking deposit blocks processed: {i}")
                break
            except KeyboardInterrupt:
                return
            except Exception as e:
                print_status('error', e)
                continue

    main_row.last_staking_deposits_update_block = i
    main_row.save()


def update_head():
    url = BEACON_API_ENDPOINT + "/eth/v1/beacon/blocks/head"
    head = requests.get(url).json()
    
    head_slot = int(head["data"]["message"]["slot"])
    head_epoch = int(head_slot / SLOTS_PER_EPOCH)
    head_block = w3.eth.get_block_number()

    cache.set("head_slot", head_slot, timeout=10000)
    cache.set("head_epoch", head_epoch, timeout=10000)
    cache.set("head_block", head_block, timeout=10000)

    return head_slot, head_epoch, head_block


def sync_up(main_row, last_slot_processed=0, loop_epoch=0, last_balance_update_time=0, reorg=False):
    print_status('info', f'syncing last_slot_processed={last_slot_processed} loop_epoch={loop_epoch} reorg={reorg}')
    
    head_slot, head_epoch, head_block = update_head()

    print_status('info', f'Head is slot={head_slot} epoch={head_epoch} block={head_block}')

    if last_slot_processed == 0:
        load_current_state(main_row)
        print_status('info', 'Setup validators')
        validator_task = process_validators_task.delay(head_slot)
        while not validator_task.ready():
            time.sleep(1)

        # recheck the previous 35 block as well to ensure there were no reorgs after shutdown
        last_slot_processed = main_row.last_slot - 35
        if last_slot_processed < 0:
            last_slot_processed = 0

        loop_epoch = int(last_slot_processed / SLOTS_PER_EPOCH)

        create_sync_committee(loop_epoch - 256)

        SNAPSHOT_CREATION_EPOCH_DELAY = SNAPSHOT_CREATION_EPOCH_DELAY_SYNC
        MEV_FETCH_DELAY_SLOTS = SLOTS_PER_EPOCH * 2

        initial_run = True
    else:
        SNAPSHOT_CREATION_EPOCH_DELAY = 3
        MEV_FETCH_DELAY_SLOTS = 4

        initial_run = False

    last_balance_snapshot_planned_date = main_row.last_balance_snapshot_planned_date
    last_missed_attestation_aggregation_epoch = main_row.last_missed_attestation_aggregation_epoch
    last_mev_reward_fetch_slot = main_row.last_mev_reward_fetch_slot

    if last_mev_reward_fetch_slot < MERGE_SLOT - 1:
        last_mev_reward_fetch_slot = MERGE_SLOT - 1

    if initial_run:
        print_status('info', 'Started up: filling epochs')
        setup_epochs(main_row, last_slot_processed, loop_epoch)

    setup_staking_deposits(main_row, head_block)

    slots_processed = 0
    start_time = time.time()
    for slot in range(last_slot_processed, head_slot+1):
        while True:
            try:
                tasks_count = wait_for_task_queue_to_clear()

                if int(slot / SLOTS_PER_EPOCH) != loop_epoch:
                    with transaction.atomic():
                        check_epoch = int(slot / SLOTS_PER_EPOCH)
                        if slot >= main_row.last_epoch_slot_processed:
                            print_status('info', f'New epoch {check_epoch}')
                            load_epoch(check_epoch, slot)
                        else:
                            if not Epoch.objects.filter(epoch=check_epoch).exists():
                                load_epoch(check_epoch, slot)

                        if not reorg:
                            if not initial_run:
                                print_status('info', 'Load current state')
                                load_current_state(main_row)

                                sec_since_last_balance_update = (time.time() - last_balance_update_time)
                                if sec_since_last_balance_update > 200:
                                    last_balance_update_time = time.time()
                                    process_validators_task.delay(slot)

                            if check_epoch > head_epoch - EPOCH_REWARDS_HISTORY_DISTANCE_SYNC - 2:
                                print_status('info', 'load epoch rewards...')
                                load_epoch_rewards_task.delay(check_epoch - 2)

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
                break

            except KeyboardInterrupt:
                return
            except Exception as e:
                print_status('error', e)
                continue
    
    return head_slot, loop_epoch, last_balance_update_time


class Command(BaseCommand):
    help = 'Starts the block listener'

    def handle(self, *args, **options):
        main_row, created = Main.objects.get_or_create(id=1, defaults={
            'last_balance_snapshot_planned_date': timezone.make_aware(datetime.fromtimestamp(0), timezone=timezone.utc),
            'finalized_checkpoint_epoch': 0,
            'justified_checkpoint_epoch': 0,
            })
        
        head_slot = 0
        last_slot_processed = -10000
        while last_slot_processed < head_slot - 128:
            last_slot_processed, loop_epoch, last_balance_update_time = sync_up(main_row)
            head_slot = update_head()[0]

        def with_urllib3(url, headers):
            import urllib3
            http = urllib3.PoolManager()
            return http.request('GET', url, preload_content=False, headers=headers)
        
        url = BEACON_API_ENDPOINT + '/eth/v1/events?topics=chain_reorg,head'
        headers = {'Accept': 'text/event-stream'}
        response = with_urllib3(url, headers)
        client = sseclient.SSEClient(response)
        last_balance_update_time = time.time()
        for event in client.events():
            if str(event.event) == "chain_reorg":
                event_data = json.loads(event.data)
                reorg_until_slot=int(event_data["slot"]) - int(event_data["depth"]) - 2
                print_status('info', f"reorg at slot {event_data['slot']} depth {event_data['depth']}, rewind to slot {reorg_until_slot}")
                print_status('info', f"reorg event: {str(event.data)}")
                loop_epoch = int((reorg_until_slot-1) / SLOTS_PER_EPOCH)
                last_slot_processed, loop_epoch, last_balance_update_time = sync_up(main_row, reorg_until_slot, loop_epoch, last_balance_update_time, True)
            else:
                last_slot_processed, loop_epoch, last_balance_update_time = sync_up(main_row, last_slot_processed+1, loop_epoch, last_balance_update_time)
