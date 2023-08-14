from django.http import JsonResponse
from django.shortcuts import render
from blockfetcher.models import Validator, AttestationCommittee, ValidatorBalance, Block, Withdrawal, Epoch, SyncCommittee
from django.core.cache import cache
from ethstakersclub.settings import CHURN_LIMIT_QUOTIENT, SLOTS_PER_EPOCH, SECONDS_PER_SLOT, BALANCE_PER_VALIDATOR, GENESIS_TIMESTAMP
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Sum, Count, F
from blockfetcher.cache import *
from django.db import connection, models
from api.util import calculate_activation_epoch, measure_execution_time, get_validator_limit


def get_blocks(request):
    range_value = int(request.GET.get('range', 10))
    direction_value = str(request.GET.get('direction', "descending"))
    from_slot = request.GET.get('from_slot')
    omit_pending = bool(request.GET.get('omit_pending', False))

    if omit_pending is not True and omit_pending is not False:
        omit_pending = False

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
        return JsonResponse({'message': 'Invalid direction value.','success': False})
    else:
        if direction_value == "ascending":
            blocks = Block.objects.filter(slot_number__gte=from_slot).order_by("-slot_number")
        else:
            blocks = Block.objects.filter(slot_number__lte=from_slot).order_by("-slot_number")
        
        if omit_pending is True:
            blocks = blocks.exclude(empty=3)

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
        if request.user.is_authenticated:
            try:
                validator_ids = [int(pk) for pk in request.user.profile.watched_validators.split(',') if pk.isdigit()]
            except:
                return JsonResponse({'success': False, 'status': 'error', 'message': 'Invalid validator ID provided.'})
        else:
            return JsonResponse({'success': False, 'status': 'error', 'message': 'Invalid validator ID provided.'})
    else:
        try:
            validator_ids = [int(id) for id in validator_ids.split(',')]
        except ValueError:
            return JsonResponse({'success': False, 'status': 'error', 'message': 'Invalid validator ID provided.'})

    for validator_id in validator_ids:
        if validator_id <= 0:
            return JsonResponse({'success': False, 'status': 'error', 'message': 'Invalid validator ID provided.'})

    unique_validators_array = list(set(validator_ids))

    if len(unique_validators_array) > get_validator_limit(request):
        return JsonResponse({'success': False, 'status': 'error', 'message': 'Too many validators added.'})
    elif len(unique_validators_array) <= 0:
        return JsonResponse({'success': False, 'status': 'error', 'message': 'No validator ids provided'})

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

    validator_count = len(validator_ids)

    slots_to_check = 5 * SLOTS_PER_EPOCH
    if validator_count > 5:
        slots_to_check = 3 * SLOTS_PER_EPOCH
    if validator_count > 10:
        slots_to_check = 2 * SLOTS_PER_EPOCH
    if validator_count > 50:
        slots_to_check = 0.4 * SLOTS_PER_EPOCH
    if validator_count >= 200:
        slots_to_check = 10

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
    elif to_slot - from_slot > slots_to_check:
        from_slot = to_slot - slots_to_check

    attestations = get_attestations(validator_ids, from_slot, to_slot)

    response = {
        'success': True,
        'data': attestations,
        'from_slot': from_slot,
        'to_slot': to_slot,
    }

    return JsonResponse(response)

def get_attestations(index_numbers, from_slot, to_slot):
    if len(index_numbers) >= 200 and (to_slot - from_slot) <= 10:
        attestations = AttestationCommittee.objects.filter(slot__gte=from_slot, slot__lte=to_slot)
    else:
        attestations = AttestationCommittee.objects.filter(slot__gte=from_slot, slot__lte=to_slot, validator_ids__overlap=index_numbers)
                        
    attestations = attestations.order_by('-slot').values('validator_ids', 'distance', 'epoch', 'slot')
    
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
def api_get_attestations_for_slots(request):
    validator_ids = extract_validator_ids(request)
    if isinstance(validator_ids, JsonResponse):
        return validator_ids
    
    from_slot = int(request.GET.get('from_slot'))
    to_slot = request.GET.get('to_slot')

    range_value = int(request.GET.get('range', 10))
    if range_value <= 0:
        return JsonResponse({'success': False, 'status': 'error', 'message': 'Invalid range. Is lower or equal to 0.'})
    elif range_value > 10:
        return JsonResponse({'success': False, 'status': 'error', 'message': 'Invalid range. Is higher than 10.'})

    include_pending = bool(request.GET.get('include_pending', False))

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
    elif to_slot - from_slot > 9:
        from_slot = to_slot - (range_value - 1)

    attestations = get_attestations_for_slots(validator_ids, from_slot, to_slot)

    response = {
        'success': True,
        'data': attestations,
        'from_slot': from_slot,
        'to_slot': to_slot,
    }

    return JsonResponse(response)


def get_attestations_for_slots(index_numbers, from_slot, to_slot):
    attestations = AttestationCommittee.objects \
                    .filter(slot__gte=from_slot,
                            slot__lte=to_slot) \
                    .values('validator_ids', 'distance', 'slot')

    validator_ids_set = set(index_numbers)
    slots = {}
    for slot in range(from_slot, to_slot+1):
        slots[slot] = {
            "epoch": int(slot / SLOTS_PER_EPOCH),
            "distance": [],
            "slot": slot,
            "block_timestamp": calc_time_of_slot(slot + 1).isoformat(),
            "validator_id": []
        }

    for attestation in attestations:
        for id in set(attestation['validator_ids']).intersection(validator_ids_set):
            slots[attestation['slot']]["distance"].append(attestation['distance'][attestation['validator_ids'].index(id)])
            slots[attestation['slot']]["validator_id"].append(id)
    
    ordered_list = sorted(list(slots.values()), key=lambda x: x["slot"], reverse=True)
    
    return ordered_list


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
    withdrawals = list(Withdrawal.objects.filter(validator__in=index_numbers).order_by("-index")[cursor_value:cursor_value+range_value]
                       .values('validator', 'address', 'amount', 'block__slot_number', 'block__timestamp'))
    
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

    participated_sync_committee = SyncCommittee.objects.filter(validator_ids__overlap=index_numbers, period__lte=sync_period_of_target_slot).order_by("-period")[:3].values("validator_ids", "period")
    participated_sync_committee_mapping = {item["period"]: item["validator_ids"] for item in participated_sync_committee}

    sync_committee_participation = []
    if len(participated_sync_committee) > 0:
        for psc in participated_sync_committee:
            remaining_items = range-len(sync_committee_participation)
            if remaining_items > range or remaining_items <= 0:
                break

            period_end = (psc["period"] + 1)*SLOTS_PER_EPOCH*256
            period_start = psc["period"]*SLOTS_PER_EPOCH*256
            
            res = list(Block.objects.filter(slot_number__lt=period_end, slot_number__lte=from_slot, slot_number__gte=period_start)
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
                    {"participated": "no_block_proposed" if int(scp["empty"]) != 3 else "pending",
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
        from_epoch = get_latest_rewards_and_penalties_epoch()
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
    rewards_penalties = []

    for epoch in reversed(range(epoch_from, epoch_to+1)):
        epoch_attestation_rewards = get_rewards_and_penalties_from_cache(index_numbers, epoch)

        if len(epoch_attestation_rewards) > 0:
            head = sum(v[0] for v in epoch_attestation_rewards)
            target = sum(v[1] for v in epoch_attestation_rewards)
            source = sum(v[2] for v in epoch_attestation_rewards)
            sync_reward = sum(v[3] for v in epoch_attestation_rewards)
            sync_penalty = sum(v[4] for v in epoch_attestation_rewards)
            block_attestations = sum(v[5] for v in epoch_attestation_rewards)
            block_sync_aggregate = sum(v[6] for v in epoch_attestation_rewards)
            block_proposer_slashings = sum(v[7] for v in epoch_attestation_rewards)
            block_attester_slashings = sum(v[8] for v in epoch_attestation_rewards)
            attestations = sum(1 for v in epoch_attestation_rewards if (v[0] + v[1] + v[2]) >= 0)
            missed_attestations = len(epoch_attestation_rewards) - attestations
            total_reward = head + target + source + sync_reward + sync_penalty + block_attestations + \
                block_sync_aggregate + block_proposer_slashings + block_attester_slashings
                    
            rewards_penalties.append(
                {
                    'epoch': epoch,
                    'head': head,
                    'target': target,
                    'source': source,
                    'sync_reward': sync_reward,
                    'sync_penalty': sync_penalty,
                    'block_attestations': block_attestations,
                    'block_sync_aggregate': block_sync_aggregate,
                    'block_proposer_slashings': block_proposer_slashings,
                    'block_attester_slashings': block_attester_slashings,
                    'attestations': attestations,
                    'missed_attestations': missed_attestations,
                    'total_reward': total_reward,
                }
            )

    return rewards_penalties


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

    history = list(
        ValidatorBalance.objects.filter(validator_id__in=index_array, date__lte=from_date, date__gt=(from_date - timedelta(days=range_value)))
        .values('date')
        .annotate(
            total_consensus_balance_sum=Sum('total_consensus_balance'),
            execution_reward_sum=Sum('execution_reward'),
            missed_attestations_sum=Sum('missed_attestations'),
            missed_sync_sum=Sum('missed_sync'),
            last_slot=F('slot')
        )
        .order_by('date')
    )

    try:
        history_last_slot = history[-1]["last_slot"]
    except:
        history_last_slot = 0
    
    active_validator_count = sum(1 for v in cached_validators if v["status"] == "active_ongoing" or v["status"] == "active_exiting" or v["status"] == "active_slashed")

    total_deposited = sum(v["deposited"] for v in cached_validators) / 1000000000

    if timezone.now().date() == from_date:
        if len(history) == 0 or (len(history) > 0 and history_last_slot < validator_update_slot):
            total_consensus_balance_sum = sum(v["total_consensus_balance"] for v in cached_validators)
            execution_reward_sum = sum(v["execution_reward"] for v in cached_validators)
            missed_attestations_sum = sum(v["missed_attestations"] for v in cached_validators)
            missed_sync_sum = sum(v["missed_sync"] for v in cached_validators)

            history.append(
                {
                    "date": timezone.now().date(),
                    "total_consensus_balance_sum": total_consensus_balance_sum,
                    "execution_reward_sum": execution_reward_sum,
                    "missed_attestations_sum": missed_attestations_sum,
                    "missed_sync_sum": missed_sync_sum,
                }
            )

    total_rewards = {"total_execution_reward": 0,
                     "total_consensus_reward": 0,
                     "total_reward": 0}

    apy = [{"execution_reward": 0,
            "consensus_reward": 0,
            "total_reward": 0,
            "consensus_apy": 0,
            "execution_apy": 0,
            "apy_sum": 0,
            "apy": 0,
            "days": d,
            "diff": timezone.now().date() - timedelta(days=d),
           } for d in [1,7,30]]

    now_date = timezone.now().date()
    chart_data_mapping = {}
    previous_balance = 0
    previous_execution_reward = 0

    for entry in history:
        if previous_balance != 0:
            balance_change = entry["total_consensus_balance_sum"] - previous_balance
            execution_reward_change = entry["execution_reward_sum"] - previous_execution_reward

            new_entry = {
                'date': entry["date"].isoformat(),
                'balance_change': float(balance_change / 1000000000),
                'execution_reward_change': float(execution_reward_change / 10**18),
                'missed_attestations_change': int(entry["missed_attestations_sum"]),
                'missed_sync_change': int(entry["missed_sync_sum"])
            }
            chart_data_mapping[entry["date"].isoformat()] = new_entry

            for e in apy:
                if entry["date"] < now_date and entry["date"] >= e["diff"]:
                    e["execution_reward"] += float(execution_reward_change / 10**18)
                    e["consensus_reward"] += float(balance_change / 1000000000)

        previous_balance = entry["total_consensus_balance_sum"]
        previous_execution_reward = entry["execution_reward_sum"]
    
    if len(history) > 0:
        total_rewards["total_execution_reward"] = (history[-1]["execution_reward_sum"] / 10**18)
        total_rewards["total_consensus_reward"] = (history[-1]["total_consensus_balance_sum"] / 1000000000) - total_deposited

    for e in apy:
        e["total_reward"] = (e["execution_reward"] + e["consensus_reward"])
        e["apy_sum"] = (e["execution_reward"] + e["consensus_reward"]) / e["days"] * 365
        e["apy"] = e["apy_sum"] / (active_validator_count * BALANCE_PER_VALIDATOR) * 100 if active_validator_count > 0 else 0
        e["consensus_apy_sum"] = e["consensus_reward"] / e["days"] * 365
        e["execution_apy_sum"] = e["execution_reward"] / e["days"] * 365
        e["consensus_apy"] = e["consensus_apy_sum"] / (active_validator_count * BALANCE_PER_VALIDATOR) * 100 if active_validator_count > 0 else 0
        e["execution_apy"] = e["execution_apy_sum"] / (active_validator_count * BALANCE_PER_VALIDATOR) * 100 if active_validator_count > 0 else 0
    
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


@measure_execution_time
def check_if_proposal_scheduled(request):
    validator_ids = extract_validator_ids(request)
    if isinstance(validator_ids, JsonResponse):
        return validator_ids

    current_slot = get_current_slot_from_cache()

    pending_blocks = Block.objects.filter(proposer__isnull=False, timestamp__gt=timezone.now(), slot_number__gt=current_slot).order_by("slot_number")

    if len(pending_blocks) > 0:
        next_proposal = pending_blocks.filter(proposer__in=validator_ids)
        if not next_proposal.exists():
            next_block_not_in = pending_blocks.last().timestamp.isoformat()
            next_block_in = 0
            proposal_scheduled = "No"
        else:
            next_block_not_in = 0
            next_block_in = next_proposal.first().timestamp.isoformat()
            proposal_scheduled = "Yes"
    else:
        next_block_not_in = 0
        next_block_in = 0
        proposal_scheduled = "update pending"

    response = {
        'success': True,
        'proposal_scheduled': proposal_scheduled,
        'next_block_not_in': next_block_not_in,
        'next_block_in': next_block_in,
    }

    return JsonResponse(response)


@measure_execution_time
def api_get_blocks_by_proposer(request):
    validator_ids = extract_validator_ids(request)
    if isinstance(validator_ids, JsonResponse):
        return validator_ids
    
    range_value = int(request.GET.get('range', 5))
    cursor_value = int(request.GET.get('cursor', 0))
    direction_value = str(request.GET.get('direction', "descending"))
    order_by = str(request.GET.get('order_by', 'slot'))
    
    if range_value > 25 or range_value < 0:
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
    elif direction_value != "ascending" and direction_value != "descending":
        return JsonResponse({'message': 'Invalid direction value.','success': False})
    elif order_by != 'slot' and order_by != 'total_reward':
        order_by = 'slot'

    blocks = get_blocks_by_proposer(validator_ids, cursor_value, range_value, direction_value, order_by)

    response = {
        'success': True,
        'data': blocks,
        'range_value': range_value,
        'cursor_value': cursor_value,
    }

    return JsonResponse(response)


def get_blocks_by_proposer(index_numbers, cursor_value, range_value, direction_value, order_by):
    blocks = Block.objects.filter(proposer__in=index_numbers)

    if order_by == "total_reward":
        if direction_value == "descending":
            blocks = blocks.order_by("-total_reward")
        else:
            blocks = blocks.order_by("total_reward")
    else:
        if direction_value == "descending":         
            blocks = blocks.order_by("-slot_number")
        else:
            blocks = blocks.order_by("slot_number")
        
    blocks = list(blocks[cursor_value:cursor_value+range_value].values('proposer', 'block_number','slot_number', 'fee_recipient', 'mev_reward_recipient',
                                                                       'timestamp', 'total_reward', 'epoch', 'mev_boost_relay', 'empty'))
    for entry in blocks:
        entry["timestamp"] = entry["timestamp"].isoformat()
        entry["total_reward"] = float(entry["total_reward"] / 10**18)

        if entry["mev_boost_relay"] != None and len(entry["mev_boost_relay"]) > 0:
            entry["fee_recipient"] = entry["mev_reward_recipient"]

    return blocks
