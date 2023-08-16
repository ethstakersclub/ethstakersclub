from celery import shared_task
from datetime import datetime
from ethstakersclub.settings import SLOTS_PER_EPOCH, MAX_SLOTS_PER_DAY, BEACON_API_ENDPOINT, ATTESTATION_EFFICIENCY_EPOCHS, \
                                    BEACON_API_ENDPOINT_OPTIONAL_GZIP, MERGE_SLOT, ACTIVE_STATUSES
from blockfetcher.models import Block, Validator, Withdrawal, StakingDeposit, SyncCommittee, MissedSync, MissedAttestation, AttestationCommittee, ValidatorBalance
from itertools import islice
from concurrent.futures import ThreadPoolExecutor, wait
from threading import Lock
from datetime import datetime
import logging
from django.utils import timezone
from django.db.models import Count, Func, F, Sum, Max
from django.core.cache import cache
from blockfetcher.beacon_api import BeaconAPI
import json
from api.util import measure_execution_time

logger = logging.getLogger(__name__)
beacon = BeaconAPI(BEACON_API_ENDPOINT_OPTIONAL_GZIP)


@measure_execution_time
def get_attestation_efficiency(epoch, validator_count):
    logger.info(f"calculate attestation efficiency for {validator_count} validators...")
    attestation_committees = list(AttestationCommittee.objects.filter(slot__gte=(epoch - ATTESTATION_EFFICIENCY_EPOCHS)*SLOTS_PER_EPOCH,
                                                                      slot__lt=(epoch + 1)*SLOTS_PER_EPOCH).values('validator_ids', 'distance'))

    count_dict = {}
    sum_dict = {}

    for i in range(validator_count):
        count_dict[i] = 0
        sum_dict[i] = 0.0

    for committee in attestation_committees:
        for validator_id, distance in zip(committee['validator_ids'], committee['distance']):
            count_dict[validator_id] += 1

            if distance == 0:
                sum_dict[validator_id] += 1.0
            elif distance != 255:
                sum_dict[validator_id] += 1.0 / (distance + 1.0)

    efficiency = {}
    total_efficiency = 0
    total_efficiency_counter = 0
    for validator_id, count in count_dict.items():
        if count > 0:
            attestation_efficiency = int(
                float(sum_dict[validator_id]) / float(count) * 10000)
            efficiency[int(validator_id)] = attestation_efficiency
            total_efficiency += attestation_efficiency
            total_efficiency_counter += 1

    average_attestation_efficiency = total_efficiency / total_efficiency_counter if total_efficiency_counter > 0 else 0
    logger.info("average attestation efficiency is " + str(average_attestation_efficiency))
    cache.set('average_attestation_efficiency', average_attestation_efficiency, timeout=5000)

    return efficiency


def assign_validators_to_staking_deposits(validators):
    logger.info("assign validators to staking deposits")

    staking_deposits = StakingDeposit.objects.filter(validator=None).values('index', 'public_key')
    staking_deposits_dict = {"0x" + str(sd['public_key']): int(sd['index']) for sd in staking_deposits}

    staking_deposits_to_update = []
    for val in validators["data"]:
        if val["validator"]["pubkey"] in staking_deposits_dict:
            staking_deposits_to_update.append(StakingDeposit(
                index=staking_deposits_dict[val["validator"]["pubkey"]],
                validator_id=val["index"],
            ))
    StakingDeposit.objects.bulk_update(staking_deposits_to_update, batch_size=512, fields=["validator"])


def update_validator_withdrawal_address(validators):
    logger.info("update validator withdrawal address")

    withdrawal_credentials = Validator.objects.filter(withdrawal_type=0).values('validator_id', 'withdrawal_credentials')
    withdrawal_credentials_dict = {w['validator_id']: str(w['withdrawal_credentials']) for w in withdrawal_credentials}

    validator_to_update = []
    for count, val in enumerate(validators["data"]):
        if int(val["index"]) in withdrawal_credentials_dict and withdrawal_credentials_dict[int(val["index"])] != str(val["validator"]["withdrawal_credentials"]):
            validator_to_update.append(Validator(
                validator_id=int(val["index"]),
                withdrawal_credentials=str(val["validator"]["withdrawal_credentials"]),
                withdrawal_type=int(str(val["validator"]["withdrawal_credentials"])[3]),
            ))
    Validator.objects.bulk_update(validator_to_update, batch_size=512, fields=["withdrawal_credentials", "withdrawal_type"])


def update_validator_activation_epochs(validators):
    logger.info("update validator activation epochs")

    activation_epochs_to_update = ["activation_epoch", "activation_eligibility_epoch"]
    for k in activation_epochs_to_update:
        kwargs = {
            k: 18446744073709551615,
        }
        epoch_undefined = Validator.objects.filter(**kwargs).values('validator_id', k)
        epoch_undefined_dict = {w['validator_id']: int(w[k]) for w in epoch_undefined}

        validator_to_update = []
        for count, val in enumerate(validators["data"]):
            if int(val["index"]) in epoch_undefined_dict and epoch_undefined_dict[int(val["index"])] != int(val["validator"][k]):
                kwargs = {
                    "validator_id": int(val["index"]),
                    k: int(val["validator"][k])
                }
                validator_to_update.append(Validator(**kwargs))
        Validator.objects.bulk_update(validator_to_update, batch_size=512, fields=[k])


def calculate_total_withdrawn_by_validator():
    logger.info("calculate total amount withdrawn for each validator")

    withdrawal_totals = Withdrawal.objects.values('validator').annotate(total_withdrawn=Sum('amount'))

    total_amount_withdrawn = {withdrawal['validator']: withdrawal['total_withdrawn'] for withdrawal in
                              withdrawal_totals}
    
    return total_amount_withdrawn


def calculate_total_execution_reward_by_validator():
    logger.info("calculate total execution reward for each validator")

    execution_totals = Block.objects.filter(empty=0, slot_number__gte=MERGE_SLOT).values('proposer').annotate(execution_total=Sum('total_reward'))

    total_execution_rewards = {block['proposer']: block['execution_total'] for block in
                               execution_totals}
    
    return total_execution_rewards


def calculate_total_deposited_by_validator():
    logger.info("calculate total deposit sum for each validator")

    deposit_totals = StakingDeposit.objects.all().values('validator_id').annotate(deposit_total=Sum('amount'))

    total_deposited = {int(d['validator_id']): int(d['deposit_total']) for d in
                               deposit_totals if d['validator_id'] is not None}
    
    return total_deposited


def calculate_validator_missed_attestations(slot):
    logger.info("calculate missed attestations at date")
    
    timestamp_target = timezone.make_aware(datetime.now(), timezone=timezone.utc).date()

    lowest_slot_at_date = 999999999
    try:
        lowest_slot_at_date_target = Block.objects.filter(slot_number__range=(slot - (MAX_SLOTS_PER_DAY + 500), slot + (MAX_SLOTS_PER_DAY + 500)), timestamp__gt=timestamp_target)\
            .order_by('slot_number').first().slot_number
    except:
        lowest_slot_at_date_target = 999999999

    validator_missed_attestations = MissedAttestation.objects.filter(slot__lt=lowest_slot_at_date, slot__gte=lowest_slot_at_date_target).values('validator_id').annotate(count=Count('validator_id'))
    validator_missed_attestations_dict = {v['validator_id']: v['count'] for v in validator_missed_attestations}

    return validator_missed_attestations_dict


def calculate_validator_missed_sync(slot):
    logger.info("calculate missed sync at date")

    timestamp_target = timezone.make_aware(datetime.now(), timezone=timezone.utc).date()

    lowest_slot_at_date = 999999999
    try:
        lowest_slot_at_date_target = Block.objects.filter(slot_number__range=(slot - (MAX_SLOTS_PER_DAY + 500), slot + (MAX_SLOTS_PER_DAY + 500)), timestamp__gt=timestamp_target)\
            .order_by('slot_number').first().slot_number
    except:
        lowest_slot_at_date_target = 999999999

    validator_missed_sync = MissedSync.objects.filter(slot__lt=lowest_slot_at_date, slot__gte=lowest_slot_at_date_target).values('validator_id').annotate(count=Count('validator_id'))
    validator_missed_sync_dict = {v['validator_id']: v['count'] for v in validator_missed_sync}

    return validator_missed_sync_dict


def calculate_validator_missed_sync_all():
    logger.info("count all missed sync")

    validator_missed_sync_all = MissedSync.objects.all().values('validator_id').annotate(count=Count('validator_id'))
    validator_missed_sync_all_dict = {v['validator_id']: v['count'] for v in validator_missed_sync_all}

    return validator_missed_sync_all_dict


def calculate_sync_committee_participation_count(slot):
    logger.info("calculate sync committee participation count")

    current_sync_period = int(int(slot / SLOTS_PER_EPOCH) / 256)
    sync_committee_participation_count = SyncCommittee.objects.filter(period__lt=current_sync_period) \
        .annotate(tag=Func(F('validator_ids'), function='unnest'))\
        .values('tag').order_by('tag').annotate(count=Count('id')).values_list('tag', 'count')
    sync_committee_participation_dict = {int(tag): int(count) for tag, count in sync_committee_participation_count}

    return sync_committee_participation_dict


def count_proposals(slot):
    logger.info("count proposed blocks")

    proposals_per_validator = Block.objects.filter(slot_number__lte=slot).values('proposer').annotate(count=Count('proposer')).values_list('proposer', 'count')
    proposals_per_validator_dict = {int(proposer): int(count) for proposer, count in proposals_per_validator if proposer is not None}

    return proposals_per_validator_dict


def count_successful_proposals(slot):
    logger.info("count successfully proposed blocks")

    proposals_per_validator = Block.objects.filter(slot_number__lte=slot, empty=0).values('proposer').annotate(count=Count('proposer')).values_list('proposer', 'count')
    proposals_per_validator_dict = {int(proposer): int(count) for proposer, count in proposals_per_validator if proposer is not None}

    return proposals_per_validator_dict


def count_proposals_after_merge(slot):
    logger.info("count proposals after merge")

    proposals_per_validator = Block.objects.filter(slot_number__lte=slot).exclude(block_number=None).values('proposer').annotate(count=Count('proposer')).values_list('proposer', 'count')
    proposals_per_validator_dict = {int(proposer): int(count) for proposer, count in proposals_per_validator if proposer is not None}

    return proposals_per_validator_dict


def calculate_highest_reward(slot):
    logger.info("calculate highest (mev) reward")

    max_reward_per_validator = Block.objects.filter(slot_number__lte=slot).exclude(block_number=None).values('proposer').annotate(max_reward=Max('total_reward')).values_list('proposer', 'max_reward')
    max_reward_per_validator_dict = {int(proposer): int(max_reward) for proposer, max_reward in max_reward_per_validator if proposer is not None}

    return max_reward_per_validator_dict


def count_withdrawals_per_validator(slot):
    logger.info("count withdrawals per validator")

    withdrawals_per_validator = Withdrawal.objects.filter(block_id__lte=slot).values('validator').annotate(count=Count('validator')).values_list('validator', 'count')
    withdrawals_per_validator_dict = {int(validator): int(count) for validator, count in withdrawals_per_validator}

    return withdrawals_per_validator_dict


def create_validators(validators):
    logger.info("create validators")

    validator_count = len(validators["data"])
    
    existing_validator_ids = set(map(int, Validator.objects.values_list('validator_id', flat=True)))
    logger.info("existing validators in db: {}".format(len(existing_validator_ids)))

    validators__to_create = iter(
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
                logger.info("created " + str(count) + " of " + str(validator_count))

    pool = ThreadPoolExecutor(max_workers=4)
    futures = []

    while True:
        batch = list(islice(validators__to_create, batch_size))
        if len(batch) == 0:
            break

        future = pool.submit(insert_batch, batch)
        futures.append(future)

    wait(futures)
    pool.shutdown()


def process_validators(slot):
    logger.info("request validators from beacon api")

    validators = beacon.get_validators(state_id=str(slot))

    create_validators(validators)

    assign_validators_to_staking_deposits(validators)
    update_validator_withdrawal_address(validators)
    update_validator_activation_epochs(validators)

    efficiency = get_attestation_efficiency(int(slot / SLOTS_PER_EPOCH) - 2, len(validators["data"]))

    total_amount_withdrawn = calculate_total_withdrawn_by_validator()
    total_execution_rewards = calculate_total_execution_reward_by_validator()
    
    sync_committee_participation_dict = calculate_sync_committee_participation_count(slot)
    validator_missed_attestations_dict = calculate_validator_missed_attestations(slot)
    validator_missed_sync_dict = calculate_validator_missed_sync(slot)

    validator_missed_sync_all_dict = calculate_validator_missed_sync_all()

    proposals_per_validator_dict = count_proposals(slot)
    successful_proposals_per_validator_dict = count_successful_proposals(slot)
    proposals_after_merge_per_validator_dict = count_proposals_after_merge(slot)

    max_reward_per_validator_dict = calculate_highest_reward(slot)

    withdrawals_per_validator_dict = count_withdrawals_per_validator(slot)

    total_deposited_dict = calculate_total_deposited_by_validator()

    pending_validators, active_validators = 0, 0
    cache_data = {}
    for count, val in enumerate(validators["data"]):
        if count % 50000 == 0:
            logger.info(f"loaded {count} of {len(validators['data'])} validators")
        
        validator = {
            "validator_id": int(val["index"]),
            "balance": int(val["balance"]),
            "status": str(val["status"]),
            "e_epoch": int(val["validator"]["exit_epoch"]),
            "w_epoch": int(val["validator"]["withdrawable_epoch"]),
            "efficiency": efficiency[int(val["index"])] if int(val["index"]) in efficiency else 0,
            "total_consensus_balance":
                int(val["balance"]) +
                int(total_amount_withdrawn[int(val["index"])] if int(val["index"]) in total_amount_withdrawn else 0),
            "execution_reward": int(total_execution_rewards[int(val["index"])] if int(val["index"]) in total_execution_rewards else 0),
            "sync_p_count": sync_committee_participation_dict[int(val["index"])] if int(val["index"]) in sync_committee_participation_dict else 0,
            "missed_attestations": validator_missed_attestations_dict[int(val["index"])] if int(val["index"]) in validator_missed_attestations_dict else 0,
            "missed_sync": validator_missed_sync_dict[int(val["index"])] if int(val["index"]) in validator_missed_sync_dict else 0,
            "missed_sync_total": validator_missed_sync_all_dict[int(val["index"])] if int(val["index"]) in validator_missed_sync_all_dict else 0,
            "pre_val": pending_validators if str(val["status"]) == "pending_queued" else -1,
            "proposals": proposals_per_validator_dict[int(val["index"])] if int(val["index"]) in proposals_per_validator_dict else 0,
            "s_proposals": successful_proposals_per_validator_dict[int(val["index"])] if int(val["index"]) in successful_proposals_per_validator_dict else 0,
            "am_proposals": proposals_after_merge_per_validator_dict[int(val["index"])] if int(val["index"]) in proposals_after_merge_per_validator_dict else 0,
            "max_reward": max_reward_per_validator_dict[int(val["index"])] if int(val["index"]) in max_reward_per_validator_dict else 0,
            "withdrawals": withdrawals_per_validator_dict[int(val["index"])] if int(val["index"]) in withdrawals_per_validator_dict else 0,
            "deposited": total_deposited_dict[int(val["index"])] if int(val["index"]) in total_deposited_dict else 0,
        }

        cache_data['validator_' + str(int(val["index"]))] = json.dumps(validator)

        if len(cache_data) > 100000:
            logger.info("bulk add validators to cache...")
            cache.set_many(cache_data, timeout=5000)
            cache_data = {}

        if str(val["status"]) == "pending_queued":
            pending_validators += 1
        elif str(val["status"]) in ACTIVE_STATUSES:
            active_validators += 1    
        
    logger.info("bulk add validators to cache...")
    cache.set_many(cache_data, timeout=5000)

    cache.set("validator_update_slot", slot, timeout=5000)
    cache.set("active_validators", active_validators, timeout=5000)