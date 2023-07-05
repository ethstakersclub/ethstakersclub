from django.http import JsonResponse
from django.shortcuts import render
from blockfetcher.models import EpochReward, Validator, AttestationCommittee, ValidatorBalance, Block, Withdrawal, Epoch, MissedAttestation, SyncCommittee, MissedSync
from django.core.cache import cache
from ethstakersclub.settings import CHURN_LIMIT_QUOTIENT, SLOTS_PER_EPOCH, SECONDS_PER_SLOT, BALANCE_PER_VALIDATOR, BEACON_API_ENDPOINT, GENESIS_TIMESTAMP, VALIDATOR_MONITORING_LIMIT
import json
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Sum
from blockfetcher.cache import *
from django.db import connection
from collections import defaultdict
from django.db import models
from api.util import calculate_activation_epoch
from api.util import measure_execution_time


def get_blocks(request):
    range_value = int(request.GET.get('range', 10))
    direction_value = str(request.GET.get('direction', "descending"))
    from_slot = request.GET.get('from_slot')

    if from_slot == 'head':
        latest_block = Block.objects.filter(proposer__isnull=False).order_by("-slot_number").first()
        from_slot = latest_block.slot_number
    else:
        from_slot = int(from_slot)

    if from_slot <= 0:
        return JsonResponse({'success': False, 'status': 'error', 'message': 'Invalid from_slot provided.'})

    if range_value > 100 or range_value < 0:
        return JsonResponse({'message': 'Invalid range value. Range must be 100 or less.','success': False})
    elif direction_value != "ascending" and direction_value != "descending":
        return JsonResponse({'message': 'Invalid cursor value.','success': False})
    else:
        if direction_value == "ascending":
            blocks = Block.objects.filter(slot_number__gte=from_slot).order_by("-slot_number")
        else:
            blocks = Block.objects.filter(slot_number__lte=from_slot).order_by("-slot_number")
        
        blocks = list(blocks[:range_value].values('proposer', 'block_number', 'slot_number', 'fee_recipient',
                                             'timestamp', 'total_reward', 'epoch', 'empty'))
        
        for entry in blocks:
            entry["timestamp"] = entry["timestamp"].isoformat()
            entry["total_reward"] = float(entry["total_reward"] / 10**18)

        return JsonResponse({
            'success': True,
            'data': blocks,
        })


class ArrayLength(models.Func):
    function = "CARDINALITY"


def get_epochs(request):
    range_value = int(request.GET.get('range', 10))
    direction_value = str(request.GET.get('direction', "descending"))
    from_epoch = request.GET.get('from_epoch')

    if from_epoch == 'head':
        latest_block = Block.objects.filter(proposer__isnull=False).order_by("-slot_number").first()
        from_epoch = latest_block.epoch
    else:
        from_epoch = int(from_epoch)

    if from_epoch <= 0:
        return JsonResponse({'success': False, 'status': 'error', 'message': 'Invalid from_epoch provided.'})

    if range_value > 100 or range_value < 0:
        return JsonResponse({'message': 'Invalid range value. Range must be 100 or less.','success': False})
    elif direction_value != "ascending" and direction_value != "descending":
        return JsonResponse({'message': 'Invalid cursor value.','success': False})
    else:
        if direction_value == "ascending":
            epochs = Epoch.objects.filter(epoch__gte=from_epoch).order_by("-epoch")
        else:
            epochs = Epoch.objects.filter(epoch__lte=from_epoch).order_by("-epoch")
        
        epochs = list(epochs[:range_value].values('epoch', 'timestamp', 'missed_attestation_count',
                                                  'total_attestations', 'participation_percent',
                                                  'epoch_total_proposed_blocks', 'average_block_reward', 'highest_block_reward'))
        
        for entry in epochs:
            entry["timestamp"] = entry["timestamp"].isoformat()
            entry["average_block_reward"] = float(entry["average_block_reward"] / 10**18) if entry["average_block_reward"] is not None else 0
            entry["highest_block_reward"] = float(entry["highest_block_reward"] / 10**18) if entry["highest_block_reward"] is not None else 0

            if entry["participation_percent"] == None:
                missed_attestations = AttestationCommittee.objects\
                .filter(slot__gte=entry["epoch"]*SLOTS_PER_EPOCH, slot__lt=(entry["epoch"] + 1)*SLOTS_PER_EPOCH)\
                .values("missed_attestation", "distance")\
                .aggregate(missed_attestation_count=Sum(ArrayLength('missed_attestation')),
                        total_attestations=Sum(ArrayLength('distance')))

                total_attestations = missed_attestations["total_attestations"] if missed_attestations["total_attestations"] != None else 0
                missed_attestation_count = missed_attestations["missed_attestation_count"] if missed_attestations["missed_attestation_count"] != None else 0

                entry["participation_percent"] = (total_attestations - missed_attestation_count) / total_attestations * 100 if total_attestations > 0 else 0
                entry["missed_attestation_count"] = missed_attestation_count
                entry["total_attestations"] = total_attestations

        return JsonResponse({
            'success': True,
            'data': epochs,
        })


def calc_time_of_slot(slot):
    return timezone.make_aware(datetime.fromtimestamp(GENESIS_TIMESTAMP + (SECONDS_PER_SLOT * slot)), timezone=timezone.utc)


def extract_validator_ids(request):
    validator_ids = request.GET.get('validators')

    if not validator_ids:
        return None

    try:
        validator_ids = [int(id) for id in validator_ids.split(',')]
    except ValueError:
        return JsonResponse({'success': False, 'status': 'error', 'message': 'Invalid validator ID provided.'})

    for validator_id in validator_ids:
        if validator_id <= 0:
            return JsonResponse({'success': False, 'status': 'error', 'message': 'Invalid validator ID provided.'})

    unique_validators_array = list(set(validator_ids))

    if len(unique_validators_array) > VALIDATOR_MONITORING_LIMIT:
        return JsonResponse({'success': False, 'status': 'error', 'message': 'Too many validators added.'})

    return unique_validators_array


@measure_execution_time
def api_get_attestations(request):
    validator_ids = extract_validator_ids(request)
    if isinstance(validator_ids, JsonResponse):
        return validator_ids
    
    from_slot = int(request.GET.get('from_slot'))

    to_slot = request.GET.get('to_slot')

    include_pending = request.GET.get('include_pending', 'auto')
    if include_pending == 'auto':
        if len(validator_ids) > 10:
            include_pending = False
        else:
            include_pending = True
    else:
        include_pending = bool(include_pending)

    epochs_to_check = 5
    if len(validator_ids) > 5:
        epochs_to_check = 3
    if len(validator_ids) > 10:
        epochs_to_check = 2
    if len(validator_ids) > 50:
        epochs_to_check = 0.4

    if to_slot == 'head':
        if include_pending:
            latest_block = Block.objects.filter(proposer__isnull=False).order_by("-slot_number").first()
        else:
            latest_block = Block.objects.filter(proposer__isnull=False).exclude(block_number=None).order_by("-slot_number").first()
        to_slot = latest_block.slot_number
    else:
        to_slot = int(to_slot)

    if to_slot - from_slot <= 0:
        return JsonResponse({'success': False, 'status': 'error', 'message': 'Invalid from_slot provided. Is higher than to_slot.'})
    elif to_slot - from_slot > (SLOTS_PER_EPOCH * epochs_to_check):
        from_slot = to_slot - (SLOTS_PER_EPOCH * epochs_to_check)

    attestations = get_attestations(validator_ids, from_slot, to_slot)

    response = {
        'success': True,
        'data': attestations,
        'from_slot': from_slot,
        'to_slot': to_slot,
    }

    return JsonResponse(response)

def get_attestations(index_numbers, from_slot, to_slot):
    attestations = AttestationCommittee.objects \
                    .filter(slot__gte=from_slot,
                            slot__lte=to_slot,
                            validator_ids__overlap=index_numbers) \
                    .values('validator_ids', 'distance', 'epoch', 'slot')\
                    .order_by('-slot') \

    '''
    query = '''
    #    SELECT u.element AS matching_number, t.distance[u.index1] AS corresponding_number, t.slot AS slot_value, t.epoch AS epoch_value
    #    FROM blockfetcher_attestationcommittee t
    #    CROSS JOIN LATERAL unnest(t.validator_ids) WITH ORDINALITY AS u(element, index1)
    #    WHERE t.slot >= %s
    #    AND t.slot <= %s
    #    AND t.validator_ids && %s
    #    AND u.element = ANY(%s)
    #    ORDER BY
    #    t.slot DESC
    '''

    with connection.cursor() as cursor:
        cursor.execute(query, [from_slot, to_slot, index_numbers, index_numbers])
        results = cursor.fetchall()

    # Process the results as needed
    for row in results:
        matching_number = row[0]
        corresponding_number = row[1]
        slot = row[2]
        epoch = row[3]
        print(matching_number)
        print(corresponding_number)
        print(slot)
        print(epoch)
        # Do something with the values
    '''
    
    validator_ids_set = set(index_numbers)
    attestation_distances = [
        {
            "epoch": attestation['epoch'],
            "distance": attestation['distance'][attestation['validator_ids'].index(id)],
            "slot": attestation['slot'],
            "block_timestamp": calc_time_of_slot(attestation['slot'] + 1).isoformat(),
            "validator_id": id
        }
        for attestation in attestations
        for id in set(attestation['validator_ids']).intersection(validator_ids_set)
    ]
    
    return attestation_distances


@measure_execution_time
def api_get_withdrawals(request):
    validator_ids = extract_validator_ids(request)
    if isinstance(validator_ids, JsonResponse):
        return validator_ids
    
    range_value = int(request.GET.get('range', 10))
    cursor_value = int(request.GET.get('cursor', 0))
    
    if range_value > 100 or range_value < 0:
        response = {
            'message': 'Invalid range value. Range must be 100 or less.',
            'success': False,
        }
        return JsonResponse(response)
    elif cursor_value < 0:
        response = {
            'message': 'Invalid cursor value.',
            'success': False,
        }
        return JsonResponse(response)

    withdrawals = get_withdrawals(validator_ids, cursor_value, range_value)

    response = {
        'success': True,
        'data': withdrawals,
        'range_value': range_value,
        'cursor_value': cursor_value,
    }

    return JsonResponse(response)


def get_withdrawals(index_numbers, cursor_value, range_value):
    withdrawals = Withdrawal.objects.filter(validator__in=index_numbers).order_by("-index")
    
    withdrawals = list(withdrawals[cursor_value:cursor_value+range_value].values('validator', 'address',
                                              'amount', 'block__slot_number',
                                              'block__timestamp'))
    for entry in withdrawals:
        entry["block__timestamp"] = entry["block__timestamp"].isoformat()
        entry["amount"] = float(entry["amount"] / 10 ** 9)

    return withdrawals


@measure_execution_time
def api_get_sync_committee_participation(request):
    validator_ids = extract_validator_ids(request)
    if isinstance(validator_ids, JsonResponse):
        return validator_ids
    
    range_value = int(request.GET.get('range', 10))
    
    if range_value > 100 or range_value < 0:
        response = {
            'message': 'Invalid range value. Range must be 100 or less.',
            'success': False,
        }
        return JsonResponse(response)
    
    from_slot = request.GET.get('from_slot')

    if from_slot == 'head':
        latest_block = Block.objects.filter(proposer__isnull=False).order_by("-slot_number").first()
        from_slot = latest_block.slot_number
    else:
        from_slot = int(from_slot)

    if from_slot <= 0:
        return JsonResponse({'success': False, 'status': 'error', 'message': 'Invalid from_slot provided.'})

    sync_committee_participation = get_sync_committee_participation(validator_ids, from_slot, range_value)

    response = {
        'success': True,
        'data': sync_committee_participation,
        'range_value': range_value,
        'from_slot': from_slot,
    }

    return JsonResponse(response)


def get_sync_committee_participation(index_numbers, from_slot, range):
    sync_period_of_target_slot = int(from_slot / (SLOTS_PER_EPOCH*256)) + 1

    participated_sync_committee = SyncCommittee.objects.filter(validator_ids__overlap=index_numbers, period__lte=sync_period_of_target_slot).order_by("-period").values("validator_ids", "period")
    participated_sync_committee_mapping = {item["period"]: item["validator_ids"] for item in participated_sync_committee}

    sync_committee_participation = []
    if len(participated_sync_committee) > 0:
        for psc in participated_sync_committee:
            remaining_items = range-len(sync_committee_participation)
            if remaining_items > range or remaining_items <= 0:
                break

            period_end = (psc["period"] + 1)*SLOTS_PER_EPOCH*256
            res = list(Block.objects.filter(slot_number__lt=period_end, slot_number__lte=from_slot)
                                    .order_by("-slot_number")[:remaining_items]
                                    .values("sync_committee_bits", "slot_number", "epoch", "empty")
                      )
            for r in res:
                r["period"] = psc["period"]
            sync_committee_participation += res

            if len(sync_committee_participation) >= range:
                break
    

    dashboard_sync_committee_participation = []
    index_numbers_set = set(index_numbers)
    for scp in sync_committee_participation:
        participation = 0
        if len(scp["sync_committee_bits"]) > 1 and int(scp["empty"]) != 2:
            hex_str = scp["sync_committee_bits"]
            binary_string = bin(int(int.from_bytes(bytes.fromhex(hex_str[2:]), byteorder="little")))[2:].zfill(
                len(hex_str[2:]) * 4)[::-1]
            participation = binary_string.count('1')
        else:
            binary_string = None

        for value in index_numbers_set.intersection(participated_sync_committee_mapping[scp["period"]]):
            index = participated_sync_committee_mapping[scp["period"]].index(value)
            if binary_string != None:
                dashboard_sync_committee_participation.append(
                    {"participated": "yes" if binary_string[index] == '1' else "no",
                        "period": scp["period"], "slot": scp["slot_number"], "epoch": scp["epoch"], "validator_id": value, "participation": participation,
                        "block_timestamp": calc_time_of_slot(scp["slot_number"]).isoformat()}
                )
            else:
                dashboard_sync_committee_participation.append(
                    {"participated": "no_block_proposed",
                        "period": scp["period"], "slot": scp["slot_number"], "epoch": scp["epoch"], "validator_id": value, "participation": participation,
                        "block_timestamp": calc_time_of_slot(scp["slot_number"]).isoformat()}
                )
    
    return dashboard_sync_committee_participation


@measure_execution_time
def api_get_rewards_and_penalties(request):
    validator_ids = extract_validator_ids(request)
    if isinstance(validator_ids, JsonResponse):
        return validator_ids
    
    range_value = int(request.GET.get('range', 5))
    
    if range_value > 10 or range_value < 0:
        response = {
            'message': 'Invalid range value. Range must be 10 or less.',
            'success': False,
        }
        return JsonResponse(response)
    
    from_epoch = request.GET.get('from_epoch')

    if from_epoch == 'head':
        latest_block = EpochReward.objects.order_by("-epoch").first()
        from_epoch = latest_block.epoch
    else:
        from_epoch = int(from_epoch)

    if from_epoch <= 0:
        return JsonResponse({'success': False, 'status': 'error', 'message': 'Invalid from_epoch provided.'})
    if from_epoch - range_value < 0:
        return JsonResponse({'success': False, 'status': 'error', 'message': 'Invalid from_epoch or range provided.'})

    rewards_and_penalties = get_rewards_and_penalties(validator_ids, from_epoch - range_value, from_epoch)

    response = {
        'success': True,
        'data': rewards_and_penalties,
        'range_value': range_value,
        'from_epoch': from_epoch,
    }

    return JsonResponse(response)


def get_rewards_and_penalties(index_numbers, epoch_from, epoch_to):
    epoch_attestation_rewards = EpochReward.objects.filter(epoch__gte=epoch_from, epoch__lte=epoch_to, validator_id__in=index_numbers)\
        .values("epoch", "attestation_head", "attestation_target", "attestation_source",
                "sync_reward", "sync_penalty", "block_attestations", "block_sync_aggregate",
                "block_proposer_slashings", "block_attester_slashings")
    
    rewards_penalties = defaultdict(
        lambda: {
            'epoch': 0,
            'head': 0,
            'target': 0,
            'source': 0,
            'total_reward': 0,
            'sync_reward': 0,
            'sync_penalty': 0,
            'block_attestations': 0,
            'block_sync_aggregate': 0,
            'block_proposer_slashings': 0,
            'block_attester_slashings': 0,
            'attestations': 0,
            'missed_attestations': 0
        }
    )

    for reward in epoch_attestation_rewards:
        rewards_penalties[reward["epoch"]]['epoch'] = int(reward["epoch"])
        rewards_penalties[reward["epoch"]]['head'] += int(reward["attestation_head"])
        rewards_penalties[reward["epoch"]]['target'] += int(reward["attestation_target"])
        rewards_penalties[reward["epoch"]]['source'] += int(reward["attestation_source"])
        rewards_penalties[reward["epoch"]]['total_reward'] += int(reward["attestation_head"]) + int(reward["attestation_target"]) + int(reward["attestation_source"])

        if reward["sync_reward"] is not None or reward["sync_penalty"] is not None:
            try:
                rewards_penalties[reward["epoch"]]['sync_reward'] += int(reward["sync_reward"])
                rewards_penalties[reward["epoch"]]['total_reward'] += int(reward["sync_reward"])
            except:
                pass
            try:
                rewards_penalties[reward["epoch"]]['sync_penalty'] += int(reward["sync_penalty"])
                rewards_penalties[reward["epoch"]]['total_reward'] += int(reward["sync_penalty"])
            except:
                pass

        if reward["block_attestations"] is not None:
            try:
                rewards_penalties[reward["epoch"]]['attestations_reward'] += int(reward["block_attestations"])
                rewards_penalties[reward["epoch"]]['total_reward'] += int(reward["block_attestations"])
            except:
                pass
            try:
                rewards_penalties[reward["epoch"]]['sync_aggregate'] += int(reward["block_sync_aggregate"])
                rewards_penalties[reward["epoch"]]['total_reward'] += int(reward["block_sync_aggregate"])
            except:
                pass
            try:
                rewards_penalties[reward["epoch"]]['proposer_slashings'] += int(reward["block_proposer_slashings"])
                rewards_penalties[reward["epoch"]]['total_reward'] += int(reward["block_proposer_slashings"])
            except:
                pass
            try:
                rewards_penalties[reward["epoch"]]['attester_slashings'] += int(reward["block_attester_slashings"])
                rewards_penalties[reward["epoch"]]['total_reward'] += int(reward["block_attester_slashings"])
            except:
                pass

        if int(reward["attestation_source"]) > 0 or int(reward["attestation_target"]) > 0 or int(reward["attestation_head"]) > 0:
            rewards_penalties[reward["epoch"]]['attestations'] += 1
        else:
            rewards_penalties[reward["epoch"]]['missed_attestations'] += 1

    ordered_rewards_penalties = sorted(rewards_penalties.values(), key=lambda x: x['epoch'], reverse=True)
    return ordered_rewards_penalties


@measure_execution_time
def api_chart_data_daily_rewards(request):
    validator_ids = extract_validator_ids(request)
    if isinstance(validator_ids, JsonResponse):
        return validator_ids
    
    range_value = int(request.GET.get('range', 5))
    
    if range_value > 90 or range_value < 0:
        response = {
            'message': 'Invalid range value. Range must be 90 or less.',
            'success': False,
        }
        return JsonResponse(response)
    
    from_date = request.GET.get('from_date')

    if from_date == 'head':
        from_date = timezone.now().date()
    else:
        try:
            naive_date = datetime.strptime(from_date, '%Y-%m-%d')
            from_date = timezone.make_aware(naive_date, timezone=timezone.utc)
        except ValueError:
            return JsonResponse({'success': False, 'status': 'error', 'message': 'Invalid date provided'})

    chart_data_daily_rewards, apy, total_rewards = get_chart_data_daily_rewards(validator_ids, from_date, range_value)

    response = {
        'success': True,
        'data': chart_data_daily_rewards,
        'range_value': range_value,
        'from_epoch': from_date.strftime('%Y-%m-%d'),
        'apy': apy,
        'total_rewards': total_rewards,
    }

    return JsonResponse(response)


def get_chart_data_daily_rewards(index_array, from_date, range_value, cached_validators=None, validator_update_slot=None):
    if cached_validators == None:
        cached_validators = get_validators_from_cache(index_array)
        validator_update_slot = get_validator_update_slot_from_cache()

    history = list(ValidatorBalance.objects.filter(validator_id__in=index_array, date__lte=from_date, date__gt=(from_date - timedelta(days=range_value)))
                   .order_by("date").values('date', 'validator_id', 'slot', 'total_consensus_balance', 'execution_reward', 'missed_attestations', 'missed_sync'))
    try:
        history_last_slot = history[-1]["slot"]
    except:
        history_last_slot = 0

    if timezone.now().date() == from_date:
        if len(history) == 0 or (len(history) > 0 and history_last_slot < validator_update_slot):
            for v in cached_validators:
                history.append(
                    {
                        "date": timezone.now().date(),
                        "validator_id": int(v["validator_id"]),
                        "slot": validator_update_slot,
                        "total_consensus_balance": v["total_consensus_balance"],
                        "execution_reward": v["execution_reward"],
                        "missed_attestations": v["missed_attestations"],
                        "missed_sync": v["missed_sync"]
                    }
                )

    try:
        history_last_slot = history[-1]["slot"]
    except:
        history_last_slot = 0

    previous_balance = None
    previous_execution_reward = None

    total_rewards = {"total_execution_reward": 0,
                     "total_consensus_reward": 0,
                     "total_reward": 0}

    apy = [{"execution_reward": 0,
            "consensus_reward": 0,
            "total_reward": 0,
            "entry_count": 0,
            "consensus_apy": 0,
            "execution_apy": 0,
            "apy_sum": 0,
            "apy": 0,
            "days": d,
            "diff": timezone.now().date() - timedelta(days=d),
           } for d in [1,7,30]]

    previous_balance = {}
    previous_execution_reward = {}
    now_date = timezone.now().date()
    chart_data_mapping = {}

    for entry in history:
        if entry["validator_id"] in previous_balance:
            balance_change = entry["total_consensus_balance"] - previous_balance[entry["validator_id"]]
            execution_reward_change = entry["execution_reward"] - previous_execution_reward[entry["validator_id"]]

            # Find existing entry with the same date in the mapping
            existing_entry = chart_data_mapping.get(entry["date"].isoformat())

            if existing_entry:
                existing_entry['balance_change'] += float(balance_change / 1000000000)
                existing_entry['execution_reward_change'] += float(execution_reward_change / 10**18)
                existing_entry['missed_attestations_change'] += int(entry["missed_attestations"])
                existing_entry['missed_sync_change'] += int(entry["missed_sync"])
            else:
                new_entry = {
                    'date': entry["date"].isoformat(),
                    'balance_change': float(balance_change / 1000000000),
                    'execution_reward_change': float(execution_reward_change / 10**18),
                    'missed_attestations_change': int(entry["missed_attestations"]),
                    'missed_sync_change': int(entry["missed_sync"])
                }
                chart_data_mapping[entry["date"].isoformat()] = new_entry

            for e in apy:
                if entry["date"] < now_date and entry["date"] >= e["diff"]:
                    e["execution_reward"] += float(execution_reward_change / 10**18)
                    e["consensus_reward"] += float(balance_change / 1000000000)
                    e["entry_count"] += 1

            if history_last_slot == entry["slot"]:
                total_rewards["total_execution_reward"] += (entry["execution_reward"] / 10**18)
                total_rewards["total_consensus_reward"] += (entry["total_consensus_balance"] / 1000000000) - BALANCE_PER_VALIDATOR

        if entry["total_consensus_balance"] >= 32 * 1000000000:
            previous_balance[entry["validator_id"]] = entry["total_consensus_balance"]
            previous_execution_reward[entry["validator_id"]] = entry["execution_reward"]

    for e in apy:
        e["total_reward"] = (e["execution_reward"] + e["consensus_reward"])
        e["apy_sum"] = (e["execution_reward"] + e["consensus_reward"]) / e["days"] * 365
        e["apy"] = e["apy_sum"] / (len(index_array) * BALANCE_PER_VALIDATOR) * 100
        e["consensus_apy_sum"] = e["consensus_reward"] / e["days"] * 365
        e["execution_apy_sum"] = e["execution_reward"] / e["days"] * 365
        e["consensus_apy"] = e["consensus_apy_sum"] / (len(index_array) * BALANCE_PER_VALIDATOR) * 100
        e["execution_apy"] = e["execution_apy_sum"] / (len(index_array) * BALANCE_PER_VALIDATOR) * 100
    
    total_rewards["total_reward"] = total_rewards["total_execution_reward"] + total_rewards["total_consensus_reward"]

    return list(chart_data_mapping.values()), apy, total_rewards


@measure_execution_time
def api_get_validators(request):
    range_value = int(request.GET.get('range', 5))
    
    if range_value > 100 or range_value < 0:
        response = {
            'message': 'Invalid range value. Range must be 10 or less.',
            'success': False,
        }
        return JsonResponse(response)
    
    cursor = int(request.GET.get('cursor'))

    if cursor < 0:
        return JsonResponse({'success': False, 'status': 'error', 'message': 'Invalid cursor provided.'})

    validators = get_validators(cursor, range_value)

    response = {
        'success': True,
        'data': validators,
        'range_value': range_value,
        'cursor': cursor,
    }

    return JsonResponse(response)


def get_validators(cursor, range_value):
    validators = Validator.objects.order_by("-validator_id")[cursor:cursor+range_value].values('public_key', 'validator_id', 'activation_epoch')

    active_validators_count = get_active_validators_count_from_cache()
    validators_per_epoch = int(active_validators_count / CHURN_LIMIT_QUOTIENT)
    validator_update_epoch = int(get_validator_update_slot_from_cache() / SLOTS_PER_EPOCH)
    
    validator_ids = validators.values_list("validator_id", flat=True)
    cached_validators = get_validators_from_cache(validator_ids)

    validator_dict = {v["validator_id"]: v for v in validators}
    validator_data = []
    for c in cached_validators:
        validator_data.append({"public_key": validator_dict[c["validator_id"]]["public_key"], "validator_id": c["validator_id"], "balance": c["balance"] / 10**9,
                               "status": c["status"], "efficiency": c["efficiency"],
                               "reward": float(c["execution_reward"] / 10**18) + ((c["total_consensus_balance"] / 1000000000) - BALANCE_PER_VALIDATOR),
                               "efficiency": c["efficiency"] / 100,
                               "activation_epoch": calculate_activation_epoch(int(c["pre_val"]) ,validator_update_epoch, validators_per_epoch, c["status"], validator_dict[c["validator_id"]]["activation_epoch"]),
                              })
    
    return validator_data