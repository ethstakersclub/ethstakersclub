from celery import shared_task
from datetime import datetime, timedelta
import requests
from ethstakersclub.settings import BEACON_API_ENDPOINT
import requests
from web3 import Web3
import asyncio
import json
import requests
from websockets import connect
from ethstakersclub.settings import DEPOSIT_CONTRACT_ADDRESS, EXECUTION_WS_API_ENDPOINT, BEACON_API_ENDPOINT, SLOTS_PER_EPOCH, \
    EXECUTION_HTTP_API_ENDPOINT, w3, SECONDS_PER_SLOT, GENESIS_TIME, MEV_BOOST_RELAYS, MAX_SLOTS_PER_DAY, GENESIS_TIMESTAMP
import requests
from blockfetcher.models import Main, Block, Validator, Withdrawal, AttestationCommittee, ValidatorBalance, EpochReward, StakingDeposit
from blockfetcher.models import Epoch, SyncCommittee, MissedSync, MissedAttestation
from web3.beacon import Beacon
import decimal
from itertools import islice
from threading import Thread
from concurrent.futures import ThreadPoolExecutor, wait
from threading import Lock
import concurrent.futures
from datetime import datetime, timedelta
import binascii
from django.db.models import Sum
from django.utils import timezone
import time
from django.db import transaction, DatabaseError, OperationalError
import traceback
from django.db.models import Min, Q, Count, Func, F
import random
import logging
from django.core.cache import cache
import gc
from collections import defaultdict
from collections import Counter
import timeout_decorator
from blockfetcher.beacon_api import BeaconAPI


beacon = BeaconAPI(BEACON_API_ENDPOINT)
logger = logging.getLogger(__name__)


@shared_task
def handle_new_block(block_data):
    # This function will be called whenever a new block arrives

    block_number = block_data['params']['result']['number']
    block_number = int(block_number, 16)
    # timestamp hash parentHash baseFeePerGas gasLimit gasUsed miner
    print(f"New block arrived! Block number: {str(block_number)}")

    url = BEACON_API_ENDPOINT + '/eth/v1/beacon/rewards/attestations/' + str(block_number)
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }
    data = '[]'

    response = requests.post(url, headers=headers, data=data)

    print(response.status_code)
    print(response.json())


@shared_task(bind=True, soft_time_limit=25, max_retries=10000, acks_late=True, reject_on_worker_lost=True, acks_on_failure_or_timeout=True)
def load_block_task(self, slot, epoch):
    try:
        load_block(slot, epoch)
    except Exception as e:
        logger.warning("An error occurred processing the slot %s.", slot, exc_info=True)
        self.retry(countdown=5)


@shared_task(bind=True, soft_time_limit=60, max_retries=10000, acks_late=True, reject_on_worker_lost=True, acks_on_failure_or_timeout=True)
def load_epoch_task(self, epoch, slot):
    try:
        load_epoch(epoch, slot)
    except Exception as e:
        logger.warning("An error occurred processing the epoch %s.", slot, exc_info=True)
        self.retry(countdown=5)


@shared_task(bind=True, soft_time_limit=10200, max_retries=10000, acks_late=True, reject_on_worker_lost=True, acks_on_failure_or_timeout=True)
def load_epoch_rewards_task(self, epoch):
    try:
        load_epoch_rewards(epoch)
    except Exception as e:
        logger.warning("An error occurred while processing the epoch rewards for epoch %s.", epoch, exc_info=True)

        self.retry(countdown=5)
    

@shared_task(bind=True, soft_time_limit=300, max_retries=10000, acks_late=True, reject_on_worker_lost=True, acks_on_failure_or_timeout=True)
def get_deposits_task(self, fromBlock, toBlock):
    try:
        get_deposits(fromBlock, toBlock)
    except Exception as e:
        logger.warning("An error occurred while processing the deposits from block %s to %s.", fromBlock, toBlock, exc_info=True)

        self.retry(countdown=5)


@shared_task(bind=True, soft_time_limit=30, max_retries=10000, acks_late=True, reject_on_worker_lost=True, acks_on_failure_or_timeout=True)
def fetch_mev_rewards_task(self, lowest_slot, cursor_slot):
    try:
        fetch_mev_rewards(lowest_slot, cursor_slot)
    except Exception as e:
        logger.warning("An error occurred while fetching MEV rewards for slot %s.", cursor_slot, exc_info=True)
        self.retry(countdown=5)


@shared_task(bind=True, soft_time_limit=120, max_retries=10000, acks_late=True, reject_on_worker_lost=True, acks_on_failure_or_timeout=True)
def epoch_aggregate_missed_attestations_and_average_mev_reward_task(self, epoch):
    try:
        epoch_aggregate_missed_attestations_and_average_mev_reward(epoch)
    except Exception as e:
        logger.warning("An error occurred while aggregating the missed attestations for epoch %s.", epoch, exc_info=True)
        self.retry(countdown=5)


@shared_task(bind=True, soft_time_limit=340, max_retries=10000, acks_late=True, reject_on_worker_lost=True, acks_on_failure_or_timeout=True)
def update_validators_task(self, slot):
    try:
        load_validators(slot)
    except Exception as e:
        logger.warning("An error occurred while updating the validators %s.", slot, exc_info=True)
        self.retry(countdown=5)


def fetch_mev_rewards(lowest_slot, cursor_slot):
    all_rewards = {}
    for key, value in MEV_BOOST_RELAYS.items():
        retry_count = 0
        while retry_count < 3:
            try:
                print(key)
                print(value)

                sl = cursor_slot
                while sl >= lowest_slot:
                    print(sl)

                    url = value + "/relay/v1/data/bidtraces/proposer_payload_delivered?limit=100&cursor=" + str(sl)
                    rewards = requests.get(url).json()

                    if len(rewards) == 0:
                        sl = -1
                        break
                    
                    print(len(rewards))

                    for r in rewards:
                        if int(r["slot"]) < lowest_slot:
                            sl = -1
                            break
                        if int(r["slot"]) not in all_rewards:
                            all_rewards[int(r["slot"])] = {"slot": int(r["slot"]), "value": decimal.Decimal(int(r["value"])),
                                                        "relay": [], "mev_reward_recipient": r["proposer_fee_recipient"]}
                        all_rewards[int(r["slot"])]["relay"].append(key)

                        if int(r["slot"]) - 1 < sl:
                            sl = int(r["slot"]) - 1
                break
            except Exception as e:
                print("An error occurred:", e)
                print(value)
                retry_count += 1

    blocks_to_update = []
    for key, r in all_rewards.items():
        blocks_to_update.append(
            Block(slot_number=int(r["slot"]), mev_reward=decimal.Decimal(int(r["value"])), 
                  mev_boost_relay=r["relay"], total_reward=decimal.Decimal(int(r["value"])),
                  mev_reward_recipient=r["mev_reward_recipient"]
                 )
        )

    Block.objects.bulk_update(blocks_to_update, fields=["mev_reward", "mev_boost_relay", "total_reward", "mev_reward_recipient"])


@transaction.atomic
def make_balance_snapshot(slot, timestamp):
    '''
    url = BEACON_API_ENDPOINT + "/eth/v1/beacon/blocks/" + str(slot)
    timestamp = requests.get(url).json()["data"]["message"]["body"]["execution_payload"]["block_hash"]
    timestamp = timezone.make_aware(datetime.fromtimestamp(timestamp), timezone=timezone.utc)

    do_snapshot = False
    with transaction.atomic():
        last_balance_snapshot = Main.objects.select_for_update().get(id=1)
        if last_balance_snapshot.last_balance_snapshot_planned_date < timestamp.date():
            do_snapshot = True
            last_balance_snapshot.last_balance_snapshot_planned_date = timestamp
            last_balance_snapshot.save()
    if do_snapshot:
        try:
    '''
    
    timestamp = timezone.make_aware(datetime.fromtimestamp(int(timestamp)), timezone=timezone.utc).date()
    timestamp_target = timestamp - timezone.timedelta(days=1)
    #timestamp_previous = timestamp_target - timezone.timedelta(days=1)

    lowest_slot_at_date = Block.objects.filter(slot_number__range=(slot - (MAX_SLOTS_PER_DAY + 300), slot + (MAX_SLOTS_PER_DAY + 300)), timestamp__gt=timestamp)\
        .order_by('slot_number').first().slot_number
    lowest_slot_at_date_target = Block.objects.filter(slot_number__range=(slot - (MAX_SLOTS_PER_DAY + 300), slot + (MAX_SLOTS_PER_DAY + 300)), timestamp__gt=timestamp_target)\
        .order_by('slot_number').first().slot_number
    
    if ValidatorBalance.objects.filter(date=timestamp_target).exists():
        print("snapshot exists on date " + str(timestamp_target) + " slot " + str(lowest_slot_at_date))

        if ValidatorBalance.objects.filter(slot=lowest_slot_at_date).exists():
            logger.info("snapshot slot matches existing one, exiting: %s.", lowest_slot_at_date)
            return
        else:
            logger.error("snapshot slot does not match existing one. new: %s.", lowest_slot_at_date)

        #previous = ValidatorBalance.objects.filter(date=timestamp_target).first().slot
        #if previous == lowest_slot_at_date:
        #    logger.info("snapshot slot matches existing one, exiting: %s.", slot)
        #    return
        #else:
        #    logger.error("snapshot slot does not match existing one: %s new: %s.", previous, lowest_slot_at_date)

    validators = beacon.get_validators(state_id=str(lowest_slot_at_date))

    print("updating historical balance of " + str(len(validators["data"])) + " validators at slot " + str(lowest_slot_at_date))

    # Query to aggregate the total amount withdrawn for each validator
    withdrawal_totals = Withdrawal.objects.filter(block__slot_number__lt=lowest_slot_at_date).values('validator').annotate(total_withdrawn=Sum('amount'))
    total_amount_withdrawn = {withdrawal['validator']: withdrawal['total_withdrawn'] for withdrawal in withdrawal_totals}

    print(131)
    validator_missed_attestations = MissedAttestation.objects.filter(slot__lt=lowest_slot_at_date, slot__gte=lowest_slot_at_date_target).values('validator_id').annotate(count=Count('validator_id'))
    validator_missed_attestations_dict = {v['validator_id']: v['count'] for v in validator_missed_attestations}
    print(132)
    validator_missed_sync = MissedSync.objects.filter(slot__lt=lowest_slot_at_date, slot__gte=lowest_slot_at_date_target).values('validator_id').annotate(count=Count('validator_id'))
    validator_missed_sync_dict = {v['validator_id']: v['count'] for v in validator_missed_sync}

    #previous_balances = ValidatorBalance.objects.filter(date=timestamp_previous).values("validator_id", "execution_reward", "total_consensus_balance")

    print(134)
    # Query to aggregate the total execution reward for each validator
    #execution_totals = Block.objects.filter(slot_number__lt=lowest_slot_at_date).values(
    #    'proposer').annotate(execution_total=Sum('total_reward'))
    execution_totals = Block.objects.filter(slot_number__lte=lowest_slot_at_date, empty=0).values(
        'proposer').annotate(execution_total=Sum('total_reward'))

    total_execution_rewards = {block['proposer']: block['execution_total'] for block in
                            execution_totals}
    print(123)
    create_validator_balances_iter = iter(
        ValidatorBalance(validator_id=int(validator["index"]),
                        date=timestamp_target,
                        balance=decimal.Decimal(int(validator["balance"])),
                        total_consensus_balance=decimal.Decimal(
                                                    int(validator["balance"]) +
                                                    (total_amount_withdrawn[int(validator["index"])] if int(validator["index"]) in total_amount_withdrawn else 0)
                                                ),
                        slot=lowest_slot_at_date,
                        execution_reward=decimal.Decimal(
                                                    (total_execution_rewards[int(validator["index"])] if int(validator["index"]) in total_execution_rewards else 0)
                                                ),
                        missed_attestations=validator_missed_attestations_dict[int(validator["index"])] if int(validator["index"]) in validator_missed_attestations_dict else 0,
                        missed_sync=validator_missed_sync_dict[int(validator["index"])] if int(validator["index"]) in validator_missed_sync_dict else 0,
                        )
        for count, validator in enumerate(validators["data"]))
    print(124)

    batch_size = 512

    def insert_batch(batch):
        ValidatorBalance.objects.bulk_create(batch, batch_size, update_conflicts=True, 
                                                update_fields=["total_consensus_balance", "slot", "balance", "execution_reward", "missed_attestations", "missed_sync"], 
                                                unique_fields=["validator_id", "date"])

    pool = ThreadPoolExecutor(max_workers=4)
    futures = []
    print(125)
    while True:
        batch = list(islice(create_validator_balances_iter, batch_size))
        if len(batch) == 0:
            break

        future = pool.submit(insert_batch, batch)
        futures.append(future)
    print(126)
    wait(futures)
    pool.shutdown()


@shared_task(bind=True, soft_time_limit=960, max_retries=10000, acks_late=True, reject_on_worker_lost=True, acks_on_failure_or_timeout=True)
def make_balance_snapshot_task(self, slot, timestamp):
    try:
        make_balance_snapshot(slot, timestamp)
    except Exception as e:
        print("error snapshot, retrying in 5 seconds")
        print(e)
        print(traceback.format_exc())

        # restart task in 5 seconds
        self.retry(countdown=5)


@transaction.atomic
def epoch_aggregate_missed_attestations_and_average_mev_reward(epoch):
    logger.info("aggregate missed attestations for epoch %s.", epoch)
    missed_attestations = AttestationCommittee.objects.filter(slot__gte=epoch*SLOTS_PER_EPOCH, slot__lt=(epoch + 1)*SLOTS_PER_EPOCH).values("slot", "epoch", "index", "missed_attestation", "distance")
    #existing_missed_attestations_for_epoch = list(MissedAttestation.objects\
    #    .filter(slot__gte=epoch*SLOTS_PER_EPOCH, slot__lt=(epoch + 1)*SLOTS_PER_EPOCH)\
    #    .values_list("validator_id", flat=True))

    missed_attestation_to_create = []
    total_attestations = 0
    for m in missed_attestations:
        total_attestations += len(m["distance"])
        if m["missed_attestation"] != None:
            for val in m["missed_attestation"]:
                missed_attestation_to_create.append(MissedAttestation(slot=m["slot"], epoch=m["epoch"], index=m["index"], validator_id=val))
                #if val in existing_missed_attestations_for_epoch:
                #    existing_missed_attestations_for_epoch.remove(val)

    missed_attestation_count = len(missed_attestation_to_create)
    participation_percent = (total_attestations - missed_attestation_count) / total_attestations * 100 if total_attestations > 0 else 0

    logger.info("calculate average mev reward %s.", epoch)
    blocks = Block.objects.filter(slot_number__gte=epoch*SLOTS_PER_EPOCH, slot_number__lt=(epoch + 1)*SLOTS_PER_EPOCH).values("total_reward", "empty", "slot_number")
    epoch_total_block_reward = 0
    epoch_total_proposed_blocks = 0
    highest_block_reward = 0
    for b in blocks:
        if b["empty"] == 0:
            epoch_total_proposed_blocks += 1
            epoch_total_block_reward += b["total_reward"]

            if b["total_reward"] > highest_block_reward:
                highest_block_reward = b["total_reward"]
        elif b["empty"] == 3:
            raise RuntimeError(f"Block {b['slot_number']} in epoch_aggregate_missed_attestations_and_average_mev_reward still not processed, waiting...")
    average_block_reward = epoch_total_block_reward / epoch_total_proposed_blocks if epoch_total_proposed_blocks > 0 else 0

    epoch_object = Epoch.objects.get(epoch=epoch)
    epoch_object.participation_percent = participation_percent
    epoch_object.missed_attestation_count = missed_attestation_count
    epoch_object.total_attestations = total_attestations
    epoch_object.epoch_total_proposed_blocks = epoch_total_proposed_blocks
    epoch_object.highest_block_reward = highest_block_reward
    epoch_object.average_block_reward = average_block_reward
    epoch_object.timestamp = timezone.make_aware(datetime.fromtimestamp(GENESIS_TIMESTAMP + (SECONDS_PER_SLOT * epoch * SLOTS_PER_EPOCH)), timezone=timezone.utc)

    logger.info("creating validator statistics %s.", epoch)
    validators = beacon.get_validators(state_id=str(epoch*SLOTS_PER_EPOCH))

    ACTIVE_STATUSES = frozenset({"active_ongoing", "active_exiting", "active_slashed"})
    PENDING_STATUSES = frozenset({"pending_queued", "pending_initialized"})
    EXITED_STATUSES = frozenset({"exited_unslashed", "exited_slashed", "withdrawal_possible", "withdrawal_done"})
    EXITING_STATUSES = frozenset({"active_exiting", "active_slashed"})

    status_list = [v["status"] for v in validators["data"]]
    status_counts = Counter(status_list)

    epoch_object.active_validators = sum(status_counts[status] for status in ACTIVE_STATUSES)
    epoch_object.pending_validators = sum(status_counts[status] for status in PENDING_STATUSES)
    epoch_object.exited_validators = sum(status_counts[status] for status in EXITED_STATUSES)
    epoch_object.exiting_validators = sum(status_counts[status] for status in EXITING_STATUSES)
    epoch_object.validators_status_json = dict(status_counts)

    epoch_object.save()

    MissedAttestation.objects.bulk_create(missed_attestation_to_create, batch_size=1024, ignore_conflicts=True)
    #if len(existing_missed_attestations_for_epoch) > 0:
    #    logger.warning("removing previously wrongly added missed attestations: count= %s", len(existing_missed_attestations_for_epoch))
    #    MissedAttestation.objects.filter(validator_id__in=existing_missed_attestations_for_epoch).delete()


@transaction.atomic
def load_block(slot, epoch):
    url = BEACON_API_ENDPOINT + "/eth/v1/beacon/blocks/" + str(slot)
    block = requests.get(url).json()
    logger.info("Process block at slot %s: %s", slot, str(block)[:200])

    if "code" in block and block["code"] == 500:
        print("api error loading block at slot " + str(slot) + ": retrying in 5 seconds")
        time.sleep(5)
        load_block(slot, epoch)
        return

    block_not_found = "message" in block and str(block["message"]) == "NOT_FOUND: beacon block at slot " + str(slot)

    if block_not_found:
        state_root = None
        print("block at slot " + str(slot) + " not found")
    else:
        state_root = block["data"]["message"]["state_root"]

    # new_block, created = Block.objects.get_or_create(slot_number=int(slot), defaults={'epoch': int(epoch)})
    try:
        new_block = Block.objects.get(slot_number=int(slot))
    except:
        new_block = Block.objects.create(slot_number=int(slot), epoch=int(epoch))

    #if block_not_found:
    #latest_block = Block.objects.filter(proposer__isnull=False).order_by("-slot_number").first()
    #block_timestamp = GENESIS_TIME + timedelta(
    #    seconds=SECONDS_PER_SLOT * slot
    #)
    #new_block.timestamp = block_timestamp
    if block_not_found and new_block.state_root != state_root:
        print("potential reorg at slot " + str(slot))
        new_block.empty = 2
        new_block.save()
        return
    elif block_not_found:
        print("block empty at slot " + str(slot))
        new_block.empty = 1
        new_block.save()
        return
    elif not block_not_found and new_block.state_root != state_root:
        new_block.empty = 0
        new_block.state_root = state_root
        new_block.deposit_count = int(block["data"]["message"]["body"]["eth1_data"]["deposit_count"])
        new_block.proposer = int(block["data"]["message"]["proposer_index"])

        new_block.parent_root = block["data"]["message"]["parent_root"]
        new_block.signature = block["data"]["signature"]
        new_block.graffiti = block["data"]["message"]["body"]["graffiti"]
        new_block.randao_reveal = block["data"]["message"]["body"]["randao_reveal"]

        url = BEACON_API_ENDPOINT + "/eth/v1/beacon/blocks/" + str(slot) + "/root"
        new_block.block_root = requests.get(url).json()["data"]["root"]

        if "sync_aggregate" in block["data"]["message"]["body"]:
            new_block.sync_committee_signature = block["data"]["message"]["body"]["sync_aggregate"]["sync_committee_signature"]
            new_block.sync_committee_bits = block["data"]["message"]["body"]["sync_aggregate"]["sync_committee_bits"]

            MissedSync.objects.filter(slot=slot).delete()

            sync_period = epoch / 256
            sync_committee = SyncCommittee.objects.get(period=sync_period)

            # Convert hex string to binary representation
            hex_str = block["data"]["message"]["body"]["sync_aggregate"]["sync_committee_bits"]
            binary_string = bin(int(int.from_bytes(bytes.fromhex(hex_str[2:]), byteorder="little")))[2:].zfill(
                len(hex_str[2:]) * 4)[::-1]

            validators_sync_missed = []
            len_binary_string = len(binary_string)

            # Iterate through the binary string and set array elements
            for count, i in enumerate(range(len_binary_string)):
                if binary_string[i] == '0':
                    validators_sync_missed.append(MissedSync(validator_id=sync_committee.validator_ids[count], period=sync_period, slot=slot))

            MissedSync.objects.bulk_create(validators_sync_missed, ignore_conflicts=True)
        if "execution_payload" in block["data"]["message"]["body"] and block["data"]["message"]["body"]["execution_payload"]["parent_hash"] != "0x0000000000000000000000000000000000000000000000000000000000000000":
            new_block.block_hash = block["data"]["message"]["body"]["execution_payload"]["block_hash"]
            new_block.fee_recipient = block["data"]["message"]["body"]["execution_payload"]["fee_recipient"]

            execution_block = w3.eth.get_block(new_block.block_hash, full_transactions=True)

            if "withdrawals" in block["data"]["message"]["body"]["execution_payload"]:
                existing_withdrawals = Withdrawal.objects.filter(block__slot_number=slot)
                if existing_withdrawals.exists():
                    existing_withdrawals.delete()

                withdrawals = block["data"]["message"]["body"]["execution_payload"]["withdrawals"]
                withdrawal_objects = [
                    Withdrawal(
                        index=withdrawal["index"],
                        amount=decimal.Decimal(withdrawal["amount"]),
                        validator=int(withdrawal["validator_index"]),
                        address=withdrawal["address"],
                        block=new_block,
                    )
                    for withdrawal in withdrawals
                ]
                Withdrawal.objects.bulk_create(withdrawal_objects)
                '''
                validator_ids = [int(withdrawal["validator_index"]) for withdrawal in withdrawals]
                validator_total_withdrawals = (
                    Withdrawal.objects.filter(validator__in=validator_ids)
                    .values("validator")
                    .annotate(total=Sum("amount"))
                )

                validator_updates = [
                    Validator(validator_id=withdrawal["validator"], total_withdrawn=decimal.Decimal(withdrawal["total"]))
                    for withdrawal in validator_total_withdrawals
                ]
                Validator.objects.bulk_update(validator_updates, fields=["total_withdrawn"])
                '''

            new_block.block_number = execution_block["number"]
            new_block.timestamp = timezone.make_aware(datetime.fromtimestamp(execution_block["timestamp"]), timezone=timezone.utc)
            parent_hash = "0x" + binascii.hexlify(execution_block["parentHash"]).decode()
            new_block.parent_hash = str(parent_hash)

            if len(execution_block["transactions"]) != 0:
                block_reward = get_block_reward(execution_block, block)
                new_block.total_reward = block_reward["total_reward"]
                new_block.fee_reward = block_reward["total_reward"]
                new_block.total_tx_fee = block_reward["total_tx_fee"]
                new_block.burnt_fee = block_reward["burnt_fee"]
            else:
                new_block.total_reward = 0
                new_block.fee_reward = 0
                new_block.total_tx_fee = 0
                new_block.burnt_fee = 0
            new_block.transaction_count = len(execution_block["transactions"])
        


        attestations = block["data"]["message"]["body"]["attestations"]

        if len(attestations) > 0:
            combinations = [
                {'slot': attestation["data"]["slot"], 'index': attestation["data"]["index"]}
                for attestation in attestations
            ]

            q_objects = Q()

            for combination in combinations:
                q_objects |= Q(**combination)
            
            except_count = 0
            while True:
                try:
                    attestation_committees_ = AttestationCommittee.objects.select_for_update().filter(q_objects)
                    break
                except:
                    if except_count < 4:
                        print("lock detected, waiting...")
                        time.sleep(1)
                        except_count += 1
                        continue
                    else:
                        print("deadlock detected, raising error...")
                        raise

            attestation_committee_dict = {}
            for ac in attestation_committees_:
                attestation_committee_dict[(ac.slot, ac.index)] = ac

            attestation_committee_update = []
            #attestation_committee_dict = {}
            for attestation in attestations:
                if (int(attestation["data"]["slot"]), int(attestation["data"]["index"])) not in attestation_committee_dict:
                    print("AttestationCommittee missing...")
                    raise
                    #while True:
                    #    except_count = 0
                    #    try:
                    #        attestation_committee = AttestationCommittee.objects.select_for_update().get(
                    #            slot=attestation["data"]["slot"],
                    #            index=attestation["data"]["index"])
                    #        attestation_committee_dict[(attestation["data"]["slot"], attestation["data"]["index"])] = attestation_committee
                    #        break
                    #    except (DatabaseError, OperationalError) as e:
                    #        if except_count < 0:
                    #            print("lock detected, waiting...")
                    #            print(e)
                    #            time.sleep(1)
                    #            except_count += 1
                    #            continue
                    #        else:
                    #            print("deadlock detected, raising error...")
                    #            print(attestation["data"]["slot"])
                    #            print(attestation["data"]["index"])
                    #            raise
                else:
                    attestation_committee = attestation_committee_dict[(int(attestation["data"]["slot"]), int(attestation["data"]["index"]))]

                # Convert hex string to binary representation
                hex_str = attestation["aggregation_bits"]
                binary_string = bin(int(int.from_bytes(bytes.fromhex(hex_str[2:]), byteorder="little")))[2:].zfill(
                    len(hex_str[2:]) * 4)[::-1]

                #if int(attestation["data"]["index"]) == 10:
                #    print(binary_string)

                distance = list(attestation_committee.distance)
                if len(distance) == 0:
                    distance = [255] * len(binary_string)

                validators_attestation_missed = []
                len_distance = len(distance)

                # Iterate through the binary string and set array elements
                for count, i in enumerate(range(len_distance)):
                    if binary_string[i] == '1':
                        dist = slot - int(attestation["data"]["slot"]) - 1
                        if dist < distance[i]:
                            distance[i] = dist
                    elif distance[i] == 255:
                        validators_attestation_missed.append(attestation_committee.validator_ids[count])

                attestation_committee.distance = list(distance)
                attestation_committee.missed_attestation = list(validators_attestation_missed)
                attestation_committee_update.append(attestation_committee)
            AttestationCommittee.objects.bulk_update(attestation_committee_update, fields=["distance", "missed_attestation"])

        new_block.save()


def send_request_post(what, data):
    url = BEACON_API_ENDPOINT + what
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }

    return requests.post(url, headers=headers, data=data).json()


#@transaction.atomic
def load_epoch_rewards(epoch):
    print("loading epoch " + str(epoch) + " consensus rewards")

    if EpochReward.objects.filter(epoch=int(epoch)).exists():
        return

    with transaction.atomic():
        attestation_rewards = send_request_post('/eth/v1/beacon/rewards/attestations/' + str(epoch), '[]')
        print(127)
            
        sync_rewards = {}
        for slot in range(epoch * SLOTS_PER_EPOCH, (epoch + 1) * SLOTS_PER_EPOCH):
            sync_rewards_json = send_request_post('/eth/v1/beacon/rewards/sync_committee/' + str(slot), '[]')
            block_not_found = "message" in sync_rewards_json and str(sync_rewards_json["message"]) == "NOT_FOUND: beacon block at slot " + str(slot)

            if not block_not_found:
                for sync_reward in sync_rewards_json["data"]:
                    validator_index = int(sync_reward["validator_index"])
                    reward = int(sync_reward["reward"])

                    if reward >= 0:
                        if validator_index in sync_rewards:
                            sync_rewards[validator_index]["reward"] += reward
                        else:
                            sync_rewards[validator_index] = {"reward": reward, "penalty": 0}
                    else:
                        reward *= -1
                        if validator_index in sync_rewards:
                            sync_rewards[validator_index]["penalty"] += reward
                        else:
                            sync_rewards[validator_index] = {"reward": 0, "penalty": reward}

        print(128)

        epoch_rewards = {}
        for reward in attestation_rewards["data"]["total_rewards"]:
            epoch_rewards[int(reward["validator_index"])] = EpochReward(
                validator_id=reward["validator_index"],
                epoch=epoch,
                attestation_head=reward["head"],
                attestation_target=reward["target"],
                attestation_source=reward["source"],
                sync_reward=sync_rewards_json[reward["validator_index"]]["reward"] if reward["validator_index"] in sync_rewards_json else None,
                sync_penalty=sync_rewards_json[reward["validator_index"]]["penalty"] if reward["validator_index"] in sync_rewards_json else None,
            )
        
        print(129)
        for slot in range(epoch * SLOTS_PER_EPOCH, (epoch + 1) * SLOTS_PER_EPOCH):
            url = BEACON_API_ENDPOINT + "/eth/v1/beacon/rewards/blocks/" + str(slot)
            block_reward = requests.get(url).json()
            block_not_found = "message" in block_reward and str(block_reward["message"]) == "NOT_FOUND: beacon block at slot " + str(slot)

            if not block_not_found:
                epoch_rewards[int(block_reward["data"]["proposer_index"])].block_attestations = int(block_reward["data"]["attestations"])
                epoch_rewards[int(block_reward["data"]["proposer_index"])].block_sync_aggregate = int(block_reward["data"]["sync_aggregate"])
                epoch_rewards[int(block_reward["data"]["proposer_index"])].block_proposer_slashings = int(block_reward["data"]["proposer_slashings"])
                epoch_rewards[int(block_reward["data"]["proposer_index"])].block_attester_slashings = int(block_reward["data"]["attester_slashings"])
        
        print(130)
        EpochReward.objects.bulk_create(epoch_rewards.values(), batch_size=512, ignore_conflicts=True)


def get_block_reward(execution_block, block):
    total_tx_fee = 0
    headers = {"Content-Type": "application/json"}

    data = [{
        "jsonrpc": "2.0",
        "method": "eth_getTransactionReceipt",
        "params": ["0x" + binascii.hexlify(t.hash).decode()],
        "id": count
    } for count, t in enumerate(execution_block["transactions"])]

    # print(str(execution_block["transactions"]))
    receipts = requests.post(EXECUTION_HTTP_API_ENDPOINT, json=data, headers=headers).json()
    #print(str(receipts))
    for r in receipts:
        #print(str(r))
        tx_fee = int(execution_block["transactions"][int(r["id"])]["gasPrice"]) * int(r["result"]["gasUsed"], 16)
        total_tx_fee += tx_fee

    base_fee = int(block["data"]["message"]["body"]["execution_payload"]["base_fee_per_gas"])
    burnt_fee = base_fee * execution_block.gasUsed
    total_reward = total_tx_fee - burnt_fee

    return {"total_reward": total_reward, "total_tx_fee": total_tx_fee, "burnt_fee": burnt_fee}


def get_attestation_performance(current_epoch):
    logger.warning("calculate attestation efficiency...")
    #past_epochs = range(current_epoch - 10, current_epoch)
    #attestation_committees = list(AttestationCommittee.objects.filter(epoch__in=past_epochs).values('validator_ids', 'distance'))
    attestation_committees = list(AttestationCommittee.objects.filter(slot__gte=(current_epoch - 10)*SLOTS_PER_EPOCH,
                                                                      slot__lt=(current_epoch + 1)*SLOTS_PER_EPOCH).values('validator_ids', 'distance'))

    performance_counts = {}

    for committee in attestation_committees:
        for i, validator_id in enumerate(committee['validator_ids']):
            if validator_id not in performance_counts:
                performance_counts[validator_id] = {"count": 0, "sum": 0, "efficiency": 0}
            performance_counts[validator_id]["count"] += 1.0

            if committee['distance'][i] == 255:
                performance_counts[validator_id]["sum"] += 0
            else:
                performance_counts[validator_id]["sum"] += 1.0 / float(committee['distance'][i] + 1.0)

    total_efficiency = 0
    for perf in performance_counts:
        attestation_efficiency = int(
            float(performance_counts[perf]["sum"]) / float(performance_counts[perf]["count"]) * 10000)
        performance_counts[int(perf)]["efficiency"] = attestation_efficiency
        total_efficiency += attestation_efficiency

    average_attestation_efficiency = total_efficiency / len(performance_counts) if len(performance_counts) > 0 else 0
    logger.warning("average attestation efficiency is " + str(average_attestation_efficiency))
    cache.set('average_attestation_efficiency', average_attestation_efficiency, timeout=5000)

    return performance_counts


def load_validators(slot):
    logger.warning("request validators from beacon api...")

    validators = beacon.get_validators(state_id=str(slot))
    validator_count = len(validators["data"])

    logger.warning("creating validators...")

    existing_validator_ids = set(Validator.objects.values_list('validator_id', flat=True))
    logger.warning("existing validators in db: " + str(len(existing_validator_ids)))

    existing_validator_ids = set(map(int, existing_validator_ids))

    created_validators_iter = iter(
        Validator(validator_id=int(validator["index"]),
                  public_key=str(validator["validator"]["pubkey"]),
                  activation_eligibility_epoch=int(validator["validator"]["activation_eligibility_epoch"]),
                  activation_epoch=int(validator["validator"]["activation_epoch"]),
                  withdrawal_credentials=str(validator["validator"]["withdrawal_credentials"]),
                  withdrawal_type=int(str(validator["validator"]["withdrawal_credentials"])[3]),
        )
        for validator in validators["data"]
        if int(validator["index"]) not in existing_validator_ids)


    batch_size = 1000
    count = 0
    progress_lock = Lock()

    def insert_batch(batch):
        Validator.objects.bulk_create(batch, batch_size, ignore_conflicts=True)
        with progress_lock:
            nonlocal count
            count += len(batch)
            if count % 10000 == 0:
                logger.warning("created " + str(count) + " of " + str(validator_count))

    pool = ThreadPoolExecutor(max_workers=4)
    futures = []

    while True:
        batch = list(islice(created_validators_iter, batch_size))
        if len(batch) == 0:
            break

        future = pool.submit(insert_batch, batch)
        futures.append(future)

    wait(futures)
    pool.shutdown()

    print("update validator withdrawal address")

    withdrawal_credentials = Validator.objects.filter(withdrawal_type=0).values('validator_id', 'withdrawal_credentials')
    print(len(withdrawal_credentials))
    withdrawal_credentials_dict = {w['validator_id']: str(w['withdrawal_credentials']) for w in withdrawal_credentials}

    validator_to_update = []
    for count, val in enumerate(validators["data"]):
        if int(val["index"]) in withdrawal_credentials_dict and withdrawal_credentials_dict[int(val["index"])] != str(val["validator"]["withdrawal_credentials"]):
            #print("does not match " + withdrawal_credentials_dict[int(val["index"])] + " - " + str(val["validator"]["withdrawal_credentials"]))
            validator_to_update.append(Validator(
                validator_id=int(val["index"]),
                withdrawal_credentials=str(val["validator"]["withdrawal_credentials"]),
                withdrawal_type=int(str(val["validator"]["withdrawal_credentials"])[3]),
            ))
    Validator.objects.bulk_update(validator_to_update, batch_size=512, fields=["withdrawal_credentials", "withdrawal_type"])

    print("update validator key epochs")

    key_epochs_to_update = ["activation_epoch", "activation_eligibility_epoch"]
    for k in key_epochs_to_update:
        kwargs = {
            k: 18446744073709551615,
        }
        epoch_undefined = Validator.objects.filter(**kwargs).values('validator_id', k)
        print(k + " - " + str(len(epoch_undefined)))
        epoch_undefined_dict = {w['validator_id']: int(w[k]) for w in epoch_undefined}

        validator_to_update = []
        for count, val in enumerate(validators["data"]):
            if int(val["index"]) in epoch_undefined_dict and epoch_undefined_dict[int(val["index"])] != int(val["validator"][k]):
                print("does not match " + str(epoch_undefined_dict[int(val["index"])]) + " - " + str(val["validator"][k]))
                kwargs = {
                    "validator_id": int(val["index"]),
                    k: int(val["validator"][k])
                }
                validator_to_update.append(Validator(**kwargs))
        Validator.objects.bulk_update(validator_to_update, batch_size=512, fields=[k])

    print("update validator information cache")

    performance_counts = get_attestation_performance(int(slot / SLOTS_PER_EPOCH) - 2)

    print("aggregate the total amount withdrawn for each validator")
    withdrawal_totals = Withdrawal.objects.values('validator').annotate(total_withdrawn=Sum('amount'))

    total_amount_withdrawn = {withdrawal['validator']: withdrawal['total_withdrawn'] for withdrawal in
                              withdrawal_totals}

    print("aggregate the total execution reward for each validator")
    execution_totals = Block.objects.filter(empty=0).values('proposer').annotate(execution_total=Sum('total_reward'))

    total_execution_rewards = {block['proposer']: block['execution_total'] for block in
                               execution_totals}
    
    current_sync_period = int(int(slot / SLOTS_PER_EPOCH) / 256)
    sync_committee_participation_count = SyncCommittee.objects.filter(period__lt=current_sync_period) \
        .annotate(tag=Func(F('validator_ids'), function='unnest'))\
        .values('tag').order_by('tag').annotate(count=Count('id')).values_list('tag', 'count')
    sync_committee_participation_mapping = {int(tag): int(count) for tag, count in sync_committee_participation_count}

    print("calculate missed attestation at date")
    timestamp = timezone.make_aware(datetime.now(), timezone=timezone.utc).date()
    timestamp_target = timestamp - timezone.timedelta(days=1)

    try:
        lowest_slot_at_date = Block.objects.filter(slot_number__range=(slot - (MAX_SLOTS_PER_DAY + 500), slot + (MAX_SLOTS_PER_DAY + 500)), timestamp__gt=timestamp)\
            .order_by('slot_number').first().slot_number
    except:
        lowest_slot_at_date = 999999999
    try:
        lowest_slot_at_date_target = Block.objects.filter(slot_number__range=(slot - (MAX_SLOTS_PER_DAY + 500), slot + (MAX_SLOTS_PER_DAY + 500)), timestamp__gt=timestamp_target)\
            .order_by('slot_number').first().slot_number
    except:
        lowest_slot_at_date_target = 999999999
    
    validator_missed_attestations = MissedAttestation.objects.filter(slot__lt=lowest_slot_at_date, slot__gte=lowest_slot_at_date_target).values('validator_id').annotate(count=Count('validator_id'))
    validator_missed_attestations_dict = {v['validator_id']: v['count'] for v in validator_missed_attestations}
    del validator_missed_attestations

    print("calculate missed sync at date")
    validator_missed_sync = MissedSync.objects.filter(slot__lt=lowest_slot_at_date, slot__gte=lowest_slot_at_date_target).values('validator_id').annotate(count=Count('validator_id'))
    validator_missed_sync_dict = {v['validator_id']: v['count'] for v in validator_missed_sync}
    del validator_missed_sync
    gc.collect()

    ACTIVE_STATUSES = frozenset({"active_ongoing", "active_exiting", "active_slashed"})

    pending_validators = 0
    active_validators = 0
    cache_data = {}
    for count, val in enumerate(validators["data"]):
        if count % 50000 == 0:
            logger.warning(f"loaded {count} of {len(validators['data'])} validators")
        
        validator = {
                     "validator_id": int(val["index"]),
                     "balance": int(val["balance"]),
                     "status": str(val["status"]),
                     "e_epoch": int(val["validator"]["exit_epoch"]),
                     "w_epoch": int(val["validator"]["withdrawable_epoch"]),
                     "efficiency": performance_counts[int(val["index"])]["efficiency"] if int(val["index"]) in performance_counts else 0,
                     "total_consensus_balance":
                         int(val["balance"]) +
                         int(total_amount_withdrawn[int(val["index"])] if int(val["index"]) in total_amount_withdrawn else 0),
                     "execution_reward": int(total_execution_rewards[int(val["index"])] if int(val["index"]) in total_execution_rewards else 0),
                     "sync_p_count": sync_committee_participation_mapping[int(val["index"])] if int(val["index"]) in sync_committee_participation_mapping else 0,
                     "missed_attestations": validator_missed_attestations_dict[int(val["index"])] if int(val["index"]) in validator_missed_attestations_dict else 0,
                     "missed_sync": validator_missed_sync_dict[int(val["index"])] if int(val["index"]) in validator_missed_sync_dict else 0,
                     "pre_val": pending_validators if str(val["status"]) == "pending_queued" else -1,
                     }

        cache_data['validator_' + str(int(val["index"]))] = str(validator)

        if len(cache_data) > 200000:
            logger.warning("bulk add validators to cache...")
            cache.set_many(cache_data, timeout=5000)
            cache_data = {}

        if str(val["status"]) == "pending_queued":
            pending_validators += 1
        elif str(val["status"]) in ACTIVE_STATUSES:
            active_validators += 1    
        

    logger.warning("bulk add validators to cache...")
    cache.set_many(cache_data, timeout=5000)
    cache.set("validator_update_slot", slot, timeout=5000)
    cache.set("active_validators", active_validators, timeout=5000)


def get_deposits(fromBlock, toBlock):
    deposit_contract = w3.eth.contract(address=DEPOSIT_CONTRACT_ADDRESS, abi=json.loads('[{"inputs":[],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"bytes","name":"pubkey","type":"bytes"},{"indexed":false,"internalType":"bytes","name":"withdrawal_credentials","type":"bytes"},{"indexed":false,"internalType":"bytes","name":"amount","type":"bytes"},{"indexed":false,"internalType":"bytes","name":"signature","type":"bytes"},{"indexed":false,"internalType":"bytes","name":"index","type":"bytes"}],"name":"DepositEvent","type":"event"},{"inputs":[{"internalType":"bytes","name":"pubkey","type":"bytes"},{"internalType":"bytes","name":"withdrawal_credentials","type":"bytes"},{"internalType":"bytes","name":"signature","type":"bytes"},{"internalType":"bytes32","name":"deposit_data_root","type":"bytes32"}],"name":"deposit","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[],"name":"get_deposit_count","outputs":[{"internalType":"bytes","name":"","type":"bytes"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"get_deposit_root","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes4","name":"interfaceId","type":"bytes4"}],"name":"supportsInterface","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"pure","type":"function"}]'))

    deposit_filter = deposit_contract.events.DepositEvent.create_filter(fromBlock=fromBlock, toBlock=toBlock)
    logs = deposit_filter.get_all_entries()

    deposits_to_create = []
    for log in logs:
        deposits_to_create.append(StakingDeposit(
            index=int.from_bytes(log.args.index, byteorder='little'),
            block_number=int(log.blockNumber),
            amount=int.from_bytes(log.args.amount, byteorder='little'),
            public_key=log.args.pubkey.hex(),
            withdrawal_credentials=log.args.withdrawal_credentials.hex(),
            signature=log.args.signature.hex(),
            transaction_index=int(log.transactionIndex),
            transaction_hash=log.transactionHash.hex(),
        ))
    StakingDeposit.objects.bulk_create(deposits_to_create, 512, update_conflicts=True, 
                                                update_fields=["block_number", "amount", "public_key", "withdrawal_credentials", 
                                                               "signature", "transaction_index", "transaction_hash"], 
                                                unique_fields=["index"])


@timeout_decorator.timeout(50)
@transaction.atomic
def load_epoch(epoch, slot):
    logger.warning("load proposals at epoch " + str(epoch) + " slot " + str(slot))

    epoch_proposer = beacon.get_proposer_duties(epoch)

    new_epoch, created = Epoch.objects.get_or_create(epoch=int(epoch),
                                                     defaults={'dependent_root': epoch_proposer["dependent_root"],
                                                               'timestamp': timezone.make_aware(datetime.fromtimestamp(GENESIS_TIMESTAMP + (SECONDS_PER_SLOT * epoch * SLOTS_PER_EPOCH)), timezone=timezone.utc)})
    
    dependent_root_not_match = new_epoch.dependent_root != epoch_proposer["dependent_root"]

    if not created and dependent_root_not_match:
        logger.warning("epoch already exists")
        new_epoch.dependent_root = epoch_proposer["dependent_root"]
        new_epoch.save()

        AttestationCommittee.objects.filter(epoch=epoch).delete()
    if created or dependent_root_not_match:
        proposals_epoch = [
            Block(
                slot_number=int(proposal["slot"]),
                epoch=epoch,
                proposer=proposal["validator_index"],
                timestamp=timezone.make_aware(datetime.fromtimestamp(GENESIS_TIMESTAMP + (SECONDS_PER_SLOT * int(proposal["slot"]))), timezone=timezone.utc)
            )
            for proposal in epoch_proposer["data"]
        ]
        Block.objects.bulk_create(proposals_epoch, batch_size=512, update_conflicts=True, update_fields=["proposer"], unique_fields=["slot_number"])

        logger.warning("load attestation committee at epoch " + str(epoch) + " slot " + str(slot))
        url = BEACON_API_ENDPOINT + '/eth/v1/beacon/states/' + str(slot) + '/committees?epoch=' + str(epoch)
        epoch_attestations = requests.get(url).json()

        logger.warning(f"Bulk create AttestationCommittee for epoch {epoch}")

        attestation_committees = [
            AttestationCommittee(
                slot=int(committee["slot"]),
                index=int(committee["index"]),
                epoch=epoch,
                validator_ids=committee["validators"],
                distance=[255]*len(committee["validators"])
            )
            for committee in epoch_attestations["data"]
        ]

        AttestationCommittee.objects.bulk_create(attestation_committees, batch_size=10000, ignore_conflicts=True)

        #for committee in epoch_attestations["data"]:
        #    attestation_committee = AttestationCommittee.objects.create(slot=int(committee["slot"]),
        #                                                                                index=int(committee["index"]),
        #                                                                                epoch=epoch,
        #                                                                                validator_ids=committee["validators"])

            #committee_validators = Validator.objects.filter(validator_id__in=list(committee["validators"]))
            #attestation_committee.validators.clear()
            #for val in committee["validators"]:
            #    attestation_committee.validators.add(val)
            #attestation_committee.save()