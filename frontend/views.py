from django.shortcuts import render
from blockfetcher.models import Validator, Block, Epoch, SyncCommittee, StakingDeposit
import time
from django.core.cache import cache
from ethstakersclub.settings import CHURN_LIMIT_QUOTIENT, SLOTS_PER_EPOCH, SECONDS_PER_SLOT, BALANCE_PER_VALIDATOR, VALIDATOR_MONITORING_LIMIT, GENESIS_TIMESTAMP
import json
from django.utils import timezone
import datetime
from django.db.models import Avg, Value
from django.utils.timesince import timesince, timeuntil
from django.http import JsonResponse
from blockfetcher.cache import *
from django.shortcuts import get_object_or_404
from api.views import get_chart_data_daily_rewards
from django.db.models.functions import TruncHour
import statistics
from api.util import calculate_activation_epoch, measure_execution_time
import re
from itertools import groupby


def calc_time_of_slot(slot):
    return timezone.make_aware(datetime.datetime.fromtimestamp(GENESIS_TIMESTAMP + (SECONDS_PER_SLOT * slot)), timezone=timezone.utc)


def get_time_diff_to_now(time):
    if timezone.now() > time:
        return timesince(time)
    else:
        return timeuntil(time)


def get_time_diff_to_now_short(time):
    return get_time_diff_to_now(time).replace("seconds", "s").replace("hours", "h").replace("minutes", "min").replace("days", "d")\
        .replace("second", "s").replace("hour", "h").replace("minute", "min").replace("day", "d")


def round_to_one_decimal_place(number):
    return round(number, 1) if number % 1 != 0 else int(number)


def print_time(start_time, pos):
    print(pos)
    print(time.time() - start_time)


@measure_execution_time
def get_slots_since_first_online(validators, current_slot):
    if len(validators) <= 0:
        return 0
    
    first_validator_online_epoch = validators[0]["activation_epoch"]
    for v in validators:
        if v["activation_epoch"] < first_validator_online_epoch:
            first_validator_online_epoch = v["activation_epoch"]
    slots_since_first_online = current_slot - (first_validator_online_epoch * SLOTS_PER_EPOCH)
    if slots_since_first_online < 0:
        slots_since_first_online = 0

    return slots_since_first_online


@measure_execution_time
def get_sync_attestation_dashboard_info(cached_validators, index_array, current_slot, current_epoch, validator_update_slot, validator_dict):
    total_attestations = 0
    sync_participation_count = 0
    try:
        for v in cached_validators:
            attestation_count = (current_epoch if v["e_epoch"] > current_epoch else v["e_epoch"]) - validator_dict.get(v["validator_id"])["activation_epoch"]
            if attestation_count > 0:
                total_attestations += attestation_count
            sync_participation_count += v["sync_p_count"]
    except:
        pass
    if total_attestations < 0:
        total_attestations = 0

    sync_duty_count = sync_participation_count * (SLOTS_PER_EPOCH * 256)
    current_sync_period = int(int(validator_update_slot / SLOTS_PER_EPOCH) / 256)
    new_sync_committees = SyncCommittee.objects.filter(period__gte=current_sync_period).values('validator_ids', 'period')[:2]
    active_sync_validators = {'validators': [], 'start': "-", 'end': "-", 'start-slot': 0, 'end-slot': 0}
    next_sync_validators = {'validators': [], 'start': "-", 'end': "-", 'start-slot': 0, 'end-slot': 0}

    for nsc in new_sync_committees:
        sync_period_start_slot = (nsc["period"]) * 256 * SLOTS_PER_EPOCH
        sync_period_end_slot = ((nsc["period"] + 1) * 256 * SLOTS_PER_EPOCH) - 1

        if current_slot < sync_period_end_slot and current_slot >= sync_period_start_slot:
            active_sync_validators["start-slot"] = sync_period_start_slot
            active_sync_validators["end-slot"] = sync_period_end_slot
            
            active_sync_validators["start"] = calc_time_of_slot(sync_period_start_slot)
            active_sync_validators["end"] = calc_time_of_slot(sync_period_end_slot)

            active_sync_validators["start_in"] = get_time_diff_to_now_short(active_sync_validators["start"])
            active_sync_validators["end_in"] = get_time_diff_to_now_short(active_sync_validators["end"])
        else:
            next_sync_validators["start-slot"] = sync_period_start_slot
            next_sync_validators["end-slot"] = sync_period_end_slot
            
            next_sync_validators["start"] = calc_time_of_slot(sync_period_start_slot)
            next_sync_validators["end"] = calc_time_of_slot(sync_period_end_slot)

            next_sync_validators["start_in"] = get_time_diff_to_now_short(next_sync_validators["start"])
            next_sync_validators["end_in"] = get_time_diff_to_now_short(next_sync_validators["end"])
        for i in index_array:
            if i in nsc["validator_ids"]:
                count = validator_update_slot - sync_period_start_slot
                sync_duty_count += count if count > 0 else 0
                sync_participation_count += 1

                if current_slot < sync_period_end_slot and current_slot >= sync_period_start_slot:
                    active_sync_validators["validators"].append(i)
                else:
                    next_sync_validators["validators"].append(i)
    
    return sync_duty_count, sync_participation_count, active_sync_validators, next_sync_validators, total_attestations


@measure_execution_time
def split_validator_ids(index, request=None):
    index_array = index.split(',')

    if len(index_array) > VALIDATOR_MONITORING_LIMIT:
        index_array[:VALIDATOR_MONITORING_LIMIT]

    validator_ids = set()
    public_keys = set()

    public_keys_pattern = re.compile(r'^(0x)?[0-9a-fA-F]{96}$')

    for item in index_array:
        if item.isdigit():
            validator_ids.add(int(item))
        elif public_keys_pattern.match(item):
            public_keys.add(item)
        else:
            print(f"Skipping invalid public key: {item}")
    
    validators = Validator.objects.filter(public_key__in=public_keys).values("public_key", "validator_id")

    for validator in validators:
        public_key = validator["public_key"]
        validator_id = validator["validator_id"]
        public_keys.remove(public_key)
        validator_ids.add(validator_id)
    
    if request is not None:
        if request.user.is_authenticated and len(validators) > 0:
            #request.user.profile.watched_validators = 
            combined = ','.join(str(x) for x in validator_ids) + ','.join(str(x) for x in public_keys)
            print(combined)

    return len(index_array), list(validator_ids), list([key[2:] if key.startswith("0x") else key for key in public_keys])


def get_validator_info(validator, cached_validator, validators_per_epoch, active_validators_count, validator_update_epoch, current_slot, add_staking_deposits=True):
    if int(cached_validator["pre_val"]) == -1:
        activation_epoch_estimate = 0
        seconds_till_activation = 0
    else:
        activation_epoch_estimate = calculate_activation_epoch(int(cached_validator["pre_val"]) ,validator_update_epoch, validators_per_epoch, cached_validator["status"], validator["activation_epoch"])
        seconds_till_activation = ((activation_epoch_estimate * SLOTS_PER_EPOCH) - current_slot) * SECONDS_PER_SLOT
    
    if add_staking_deposits:
        staking_deposits = Validator.objects.filter(validator_id=int(validator["validator_id"])).first().stakingdeposit_set.all()
    else:
        staking_deposits = []
    
    validator_info = {
                "public_key": str(validator["public_key"]),
                "validator_id": int(validator["validator_id"]),
                "w_cred": str(validator["withdrawal_credentials"]),
                "w_cred_type": str(validator["withdrawal_credentials"])[:26],
                "w_cred_address": str(validator["withdrawal_credentials"])[26:],
                "balance": float(cached_validator["balance"] / 10**9),
                "status": str(cached_validator["status"]),
                "e_epoch": int(cached_validator["e_epoch"]),
                "w_epoch": int(cached_validator["w_epoch"]),
                "activation_eligibility_epoch": int(validator["activation_eligibility_epoch"]),
                "activation_epoch": int(validator["activation_epoch"]),
                "activation_epoch_estimate": activation_epoch_estimate,
                "seconds_till_activation": seconds_till_activation if seconds_till_activation > 0 else 0,
                "pre_val": int(cached_validator["pre_val"]),
                "validators_per_epoch": validators_per_epoch,
                "next_increase_validators_per_epoch": CHURN_LIMIT_QUOTIENT - (active_validators_count - (validators_per_epoch * CHURN_LIMIT_QUOTIENT)),
                "staking_deposits": staking_deposits,
                }

    return validator_info


def get_validator_info_from_deposit(deposits, validators_per_epoch, active_validators_count, add_staking_deposits=True):
    balance = 0
    for d in deposits:
        public_key = d.public_key
        withdrawal_credentials = d.withdrawal_credentials
        balance += d.amount

    validator_info = {
                "public_key": public_key,
                "validator_id": "pending",
                "w_cred": withdrawal_credentials,
                "w_cred_type": withdrawal_credentials[:26],
                "w_cred_address": withdrawal_credentials[26:],
                "balance": float(balance / 10**9),
                "status": "deposited",
                "e_epoch": "pending",
                "w_epoch": "pending",
                "activation_eligibility_epoch": "pending",
                "activation_epoch": "pending",
                "activation_epoch_estimate": "pending",
                "seconds_till_activation": "pending",
                "pre_val": "pending",
                "validators_per_epoch": validators_per_epoch,
                "next_increase_validators_per_epoch": CHURN_LIMIT_QUOTIENT - (active_validators_count - (validators_per_epoch * CHURN_LIMIT_QUOTIENT)),
                "staking_deposits": deposits if add_staking_deposits else [],
                }

    return validator_info


@measure_execution_time
def get_efficiency_and_dashboard_head_info(cached_validators):
    dashboard_head_data = {"active_validators":0, "queued_validators":0, "exited_validators":0}
    efficiency_sum = 0
    count_efficiency = 0
    for cv in cached_validators:
        if cv["status"] == "active_ongoing" or cv["status"] == "active_exiting" or cv["status"] == "active_slashed":
            dashboard_head_data["active_validators"] += 1
            efficiency_sum += cv["efficiency"] / 100 if "efficiency" in cv else 0
            count_efficiency += 1
        elif cv["status"] == "pending_queued" or cv["status"] == "pending_initialized":
            dashboard_head_data["queued_validators"] += 1
        elif cv["status"] == "exited_unslashed" or cv["status"] == "exited_slashed" or cv["status"] == "withdrawal_possible" or cv["status"] == "withdrawal_done":
            dashboard_head_data["exited_validators"] += 1
    efficiency = (efficiency_sum / count_efficiency) if count_efficiency > 0 else 0

    return dashboard_head_data, efficiency


@measure_execution_time
def view_validator(request, index, dashboard=False):
    validators_monitored_count, validator_ids, public_keys = split_validator_ids(index, request)
    
    cached_validators = get_validators_from_cache(validator_ids)

    validator_update_slot = get_validator_update_slot_from_cache()
    current_epoch = get_current_epoch_from_cache()
    current_slot = get_current_slot_from_cache()
    active_validators_count = get_active_validators_count_from_cache()
    validators_per_epoch = int(active_validators_count / CHURN_LIMIT_QUOTIENT)
    validator_update_epoch = int(get_validator_update_slot_from_cache() / SLOTS_PER_EPOCH)

    validators = Validator.objects.filter(validator_id__in=validator_ids)\
        .values("public_key", "activation_epoch", "validator_id", "withdrawal_credentials", "activation_eligibility_epoch")
    validator_dict = {v["validator_id"]: v for v in validators}

    print(validator_dict.values())

    deposits = StakingDeposit.objects.filter(public_key__in=public_keys)
    deposits_grouped = {}
    for key, group in groupby(deposits, key=lambda x: x.public_key):
        deposits_grouped[key] = list(group)
    
    pending_validators_info = []
    for dg in deposits_grouped.values():
        pending_validators_info.append(get_validator_info_from_deposit(dg, validators_per_epoch, active_validators_count, add_staking_deposits=False))

    if dashboard == False:
        if validators_monitored_count > 1:
            dashboard = True
            validator_info = {}
        else:
            if len(validators) >= 1:
                validator_info = get_validator_info(validators[0], cached_validators[0], validators_per_epoch, active_validators_count, validator_update_epoch, current_slot)
            else:
                deposits = StakingDeposit.objects.filter(public_key=public_keys[0]).order_by('index')

                validator_info = get_validator_info_from_deposit(deposits, validators_per_epoch, active_validators_count)
    else:
        validator_info = {}
    
    chart_data, apy, total_rewards = get_chart_data_daily_rewards(validator_ids, timezone.now().date(), 45, cached_validators, validator_update_slot)

    dashboard_head_data, efficiency = get_efficiency_and_dashboard_head_info(cached_validators)
    dashboard_head_data["queued_validators"] += len(public_keys)

    sync_duty_count, sync_participation_count, active_sync_validators, next_sync_validators, total_attestations = \
        get_sync_attestation_dashboard_info(cached_validators, validator_ids, current_slot, current_epoch, validator_update_slot, validator_dict)

    slots_since_first_online = get_slots_since_first_online(validators, current_slot)

    validator_overview = []
    missed_sync_committee_duties = 0
    proposed_blocks_count = 0
    block_count = 0
    highest_execution_reward = 0
    after_merge_blocks_count = 0
    withdrawals_count = 0
    for c in cached_validators:
        if c["status"] == "pending_queued" or c["status"] == "pending_initialized":
            pending_validators_info.append(get_validator_info(validator_dict[c["validator_id"]], c, validators_per_epoch, active_validators_count, validator_update_epoch, current_slot, add_staking_deposits=False))
        else:
            missed_sync_committee_duties += int(c["missed_sync_total"])
            missed_sync_committee_duties += int(c["missed_sync"])

            proposed_blocks_count += int(c["s_proposals"])
            block_count += int(c["proposals"])
            after_merge_blocks_count += int(c["am_proposals"])
            withdrawals_count += int(c["withdrawals"])

            if c["max_reward"] > highest_execution_reward:
                highest_execution_reward = c["max_reward"]

        validator_overview.append({"public_key": validator_dict[c["validator_id"]]["public_key"], "validator_id": c["validator_id"], "balance": c["balance"],
                          "status": c["status"], "efficiency": c["efficiency"],
                          "reward": float(c["execution_reward"] / 10**18) + ((c["total_consensus_balance"] / 1000000000) - BALANCE_PER_VALIDATOR),
                          "blocks": int(c["proposals"]),
                         })
    
    block_proposal_efficiency = int(proposed_blocks_count / block_count * 100) if block_count > 0 else 100
    average_execution_reward = total_rewards["total_execution_reward"] / after_merge_blocks_count if after_merge_blocks_count > 0 else 0
    highest_execution_reward /= 10**18

    sync_duty_completed_count = sync_duty_count - missed_sync_committee_duties

    context = {
        'dashboard': dashboard,
        'validator_count': len(validator_ids),
        'total_monitored_count': len(validator_ids) + len(public_keys),
        'efficiency': round_to_one_decimal_place(efficiency),
        'efficiency_lag': 100 - efficiency,
        'chart_data': json.dumps(chart_data),
        'withdrawals_count': withdrawals_count,
        'block_count': block_count,
        'proposed_blocks_count': proposed_blocks_count,
        'block_proposal_efficiency': round_to_one_decimal_place(block_proposal_efficiency),
        'block_proposal_efficiency_lag': 100 - block_proposal_efficiency,
        'average_execution_reward': average_execution_reward,
        'highest_execution_reward': highest_execution_reward,
        'average_attestation_efficiency': get_average_attestation_efficiency_from_cache() / 100,
        'total_attestations': total_attestations,
        'apy': apy,
        'total_rewards': total_rewards,
        'missed_sync_committee_duties': missed_sync_committee_duties,
        'sync_participation_count': sync_participation_count,
        'sync_duty_count': sync_duty_count,
        'sync_duty_completed_count': sync_duty_completed_count,
        'sync_efficiency': round_to_one_decimal_place(sync_duty_completed_count / sync_duty_count * 100) if sync_duty_count > 0 else "100",
        'active_sync_validators': active_sync_validators,
        'next_sync_validators': next_sync_validators,
        'validator_overview': json.dumps(list(validator_overview)),
        'pending_validators_exist': True if len(pending_validators_info) > 0 else False,
        'pending_validators_info': json.dumps(pending_validators_info),
        'dashboard_head_data': dashboard_head_data,
        'validator_array': ','.join(map(str, validator_ids)),
        'validator_info': validator_info,
        'slots_since_first_online': slots_since_first_online,
    }
    view = render(request, 'frontend/validator_dashboard.html', context)

    return view


@measure_execution_time
def show_slots(request):
    avg_rewards_slots = list(Epoch.objects.exclude(average_block_reward=None).annotate(hour=TruncHour('timestamp')).values('hour')\
                                     .annotate(average_reward=Avg('average_block_reward')).order_by('-hour')[:1080])[::-1]

    average_by_hour = {}
    colors_by_hour = ["#2c5173","#326576","#376d79","#3d757c","#42817f","#478a82","#4c9385","#529c89","#57a58c","#5cae8f","#61b793","#66c096","#6bca99","#71d39c","#76dc9f","#7be5a2","#80eea6","#85f7a9","#8bf0ac","#90f9af","#95f2b2","#9aebb6","#9ff4b9","#a4fdbd","#aafee0"]
    for entry in reversed(avg_rewards_slots):
        if entry["hour"] == None or entry["average_reward"] == None:
            del entry
        else:
            if entry["hour"].hour not in average_by_hour:
                average_by_hour[entry["hour"].hour] = {"total": 0, "count": 0, "average": 0,
                                                       "hour": entry["hour"].hour, "color": colors_by_hour[entry["hour"].hour],
                                                       "label": str(entry["hour"].hour) + ":00", "rewards": [], "median": 0}
            average_by_hour[entry["hour"].hour]["total"] += float(entry["average_reward"] / 10**18)
            average_by_hour[entry["hour"].hour]["count"] += 1
            average_by_hour[entry["hour"].hour]["rewards"].append(float(entry["average_reward"] / 10**18))

            entry["hour"] = entry["hour"].strftime("%Y-%m-%d %H:%M")
            entry["average_reward"] = float(entry["average_reward"] / 10**18)

    for a in average_by_hour:
        average_by_hour[a]["average"] = average_by_hour[a]["total"] / average_by_hour[a]["count"]
        average_by_hour[a]["median"] = statistics.median(average_by_hour[a]["rewards"])

    context = {
        'avg_rewards_slots': json.dumps(avg_rewards_slots),
        'average_by_hour': sorted(average_by_hour.values(), key=lambda x: x["median"]),
    }
    view = render(request, 'frontend/slots.html', context)

    return view


@measure_execution_time
def show_epochs(request):
    participation_percent_epoch = list(Epoch.objects.order_by('-epoch').exclude(participation_percent=None).values('participation_percent', 'epoch')[:200])[::-1]

    context = {
        'participation_percent_epoch': json.dumps(participation_percent_epoch),
    }
    view = render(request, 'frontend/epochs.html', context)

    return view


@measure_execution_time
def show_validators(request):
    validator_count = Validator.objects.all().count()
        
    validators_chart_data = list(Epoch.objects.exclude(active_validators=None).values('timestamp', 'epoch')\
                                     .annotate(average_active_validators=Avg('active_validators'), average_exited_validators=Avg('exited_validators'),
                                               average_pending_validators=Avg('pending_validators'), average_exiting_validators=Avg('exiting_validators'))\
                                                .order_by('-epoch')[:1080])[::-1]
    
    for entry in validators_chart_data:
        entry["timestamp"] = entry["timestamp"].isoformat()

    context = {
        'validator_count': validator_count,
        'validators_chart_data': json.dumps(validators_chart_data),
    }
    view = render(request, 'frontend/validators.html', context)

    return view


@measure_execution_time
def landing_page(request):
    validators_chart_data = list(Epoch.objects.exclude(active_validators=None).values('timestamp').annotate(hour=TruncHour('timestamp')).values('hour')\
                                     .annotate(average_active_validators=Avg('active_validators'), average_exited_validators=Avg('exited_validators'),
                                               average_pending_validators=Avg('pending_validators'), average_exiting_validators=Avg('exiting_validators'))\
                                                .order_by('-hour')[:300])[::-1]
    
    for entry in validators_chart_data:
        entry["hour"] = entry["hour"].isoformat()

    latest_epoch_stats = Epoch.objects.exclude(active_validators=None).order_by('-epoch').first()
    
    active_validators = int(latest_epoch_stats.active_validators)
    pending_validators = int(latest_epoch_stats.pending_validators)
    exiting_validators = int(latest_epoch_stats.exiting_validators)

    validator_onboarding_per_epoch = int(active_validators / CHURN_LIMIT_QUOTIENT)
    next_validator_onboarding_increase = ((validator_onboarding_per_epoch + 1) * CHURN_LIMIT_QUOTIENT) - (validator_onboarding_per_epoch * CHURN_LIMIT_QUOTIENT)

    finish_activation_queue_seconds = (pending_validators / validator_onboarding_per_epoch) * SLOTS_PER_EPOCH * SECONDS_PER_SLOT
    if finish_activation_queue_seconds <= 0:
        finish_activation_queue_seconds = 1
    finish_exit_queue_seconds = (exiting_validators / validator_onboarding_per_epoch) * SLOTS_PER_EPOCH * SECONDS_PER_SLOT

    def format_time(seconds):
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        if days > 1:
            return f"{int(days)} {'days' if days != 1 else 'day'}, {int(hours)} {'hours' if hours != 1 else 'hour'}"
        elif hours > 1:
            return f"{int(hours)} {'hours' if hours != 1 else 'hour'}, {int(minutes)} min"
        else:
            return f"{int(minutes)} minutes"

    finish_activation_queue_time = format_time(finish_activation_queue_seconds)
    finish_exit_queue_time = format_time(finish_exit_queue_seconds)

    context = {
        'validators_chart_data': json.dumps(validators_chart_data),
        'pending_validators': pending_validators,
        'active_validators': active_validators,
        'exiting_validators': exiting_validators,
        'validator_onboarding_per_epoch': validator_onboarding_per_epoch,
        'next_validator_onboarding_increase': next_validator_onboarding_increase,
        'finish_activation_queue_time': finish_activation_queue_time,
        'finish_exit_queue_time': finish_exit_queue_time,
    }
    view = render(request, 'frontend/landing.html', context)

    return view


@measure_execution_time
def search_results(request):
    query = request.GET.get('query')

    results = []
    if query.startswith('0x') and len(query) > 5:
        validators = Validator.objects.filter(public_key__startswith=query)[:10].values("public_key", "validator_id")
        
        for v in validators:
            results.append({'type': 'Validator', 'text': "(" + str(v["validator_id"]) + ") " + v["public_key"], 'url': '/validator/' + str(v["validator_id"])})
        
    elif query.isdigit():
        validators = Validator.objects.filter(validator_id=int(query))[:10].values("public_key", "validator_id")
        
        for v in validators:
            results.append({'type': 'Validator', 'text': "(" + str(v["validator_id"]) + ") " + v["public_key"], 'url': '/validator/' + str(v["validator_id"])})

    return JsonResponse({'results': results})


@measure_execution_time
def search_validator_results(request):
    query_list = request.GET.get('query').split(',')
    
    validators = []
    if len(query_list) == 1:
        if query_list[0].startswith('0x') and len(query_list[0]) > 5:
            validators = Validator.objects.filter(public_key__startswith=query_list[0])[:10].values("public_key", "validator_id")

            if len(validators) == 0:
                print(12212)
                validators = StakingDeposit.objects.filter(public_key__startswith=query_list[0][2:])[:10].values("public_key", "validator_id")
                print(validators)
        elif query_list[0].isdigit():
            validators = Validator.objects.filter(validator_id=int(query_list[0]))[:10].values("public_key", "validator_id")
    else:
        validators_count, validator_ids, public_keys = split_validator_ids(request.GET.get('query'))
        validators = []

        if len(public_keys) > 0:
            validators += StakingDeposit.objects.filter(public_key__in=public_keys).values("public_key", "validator_id")
        if len(validator_ids) > 0:
            validators += Validator.objects.filter(validator_id__in=validator_ids).values("public_key", "validator_id")

    
    results = []
    for v in validators:
        if v["validator_id"] != None:
            cached_validator = get_validator_from_cache(v["validator_id"])
            results.append({'text': "(" + str(v["validator_id"]) + ") " + v["public_key"], 'validator_id': v["validator_id"], 'public_key': v["public_key"],
                            'status': cached_validator['status'] if 'status' in cached_validator else "unknown",
                            'new': True})
        else:
            results.append({'text': "(pending) " + v["public_key"], 'validator_id': 'pending', 'public_key': v["public_key"],
                            'status': "deposited",
                            'new': True})
    
    return JsonResponse({'results': results, 'array': len(query_list) > 1})


@measure_execution_time
def dashboard_empty(request):
    if request.user.is_authenticated:
        #try:
            validator_array = [pk for pk in request.user.profile.watched_validators.split(',')]
            if len(validator_array) > 0:
                return view_validator(request, ','.join(str(x) for x in validator_array), True)
        #except:
        #    pass

    context = {
        'dashboard': True,
        'validator_count': 0,
        'dashboard_head_data': {"active_validators":0, "queued_validators":0, "exited_validators":0},
        'validator_overview': json.dumps(list([])),
    }
    view = render(request, 'frontend/validator_dashboard.html', context)

    return view


@measure_execution_time
def attestation_live_monitoring_empty(request):
    if request.user.is_authenticated:
        validator_array = [int(pk) for pk in request.user.profile.watched_validators.split(',') if pk.isdigit()]
        if len(validator_array) > 0:
            return attestation_live_monitoring(request, ','.join(str(x) for x in validator_array))

    context = {
        'validator_count': 0,
    }
    view = render(request, 'frontend/live_monitoring.html', context)

    return view


@measure_execution_time
def sync_live_monitoring_empty(request):
    if request.user.is_authenticated:
        validator_array = [int(pk) for pk in request.user.profile.watched_validators.split(',') if pk.isdigit()]
        if len(validator_array) > 0:
            return sync_live_monitoring(request, ','.join(str(x) for x in validator_array))

    context = {
        'validator_count': 0,
    }
    view = render(request, 'frontend/sync_live_monitoring.html', context)

    return view


@measure_execution_time
def attestation_live_monitoring(request, index):
    validator_array = [int(pk) for pk in index.split(',')]

    current_epoch = get_current_epoch_from_cache()

    chart_data, apy, total_rewards = get_chart_data_daily_rewards(validator_array, timezone.now().date(), 30)
    
    cached_validators = get_validators_from_cache(validator_array)
    validators = Validator.objects.filter(validator_id__in=validator_array).values("public_key", "activation_epoch", "validator_id")
    validator_dict = {v["validator_id"]: v for v in validators}

    total_attestations = 0
    try:
        for v in cached_validators:
            total_attestations += (current_epoch if v["e_epoch"] > current_epoch else v["e_epoch"]) - validator_dict.get(v["validator_id"])["activation_epoch"]
    except:
        pass
    if total_attestations < 0:
        total_attestations = 0

    current_slot = get_current_slot_from_cache()
    slots_since_first_online = get_slots_since_first_online(validators, current_slot)

    context = {
        'validator_array': ','.join(map(str, validator_array)),
        'validator_count': len(validator_array),
        'chart_data': json.dumps(chart_data),
        'total_attestations': total_attestations,
        'slots_since_first_online': slots_since_first_online,
    }
    view = render(request, 'frontend/live_monitoring.html', context)

    return view


@measure_execution_time
def sync_live_monitoring(request, index):
    validator_array = [int(pk) for pk in index.split(',')]

    current_epoch = get_current_epoch_from_cache()
    current_slot = get_current_slot_from_cache()

    cached_validators = get_validators_from_cache(validator_array)
    validator_update_slot = get_validator_update_slot_from_cache()
    validators = Validator.objects.filter(validator_id__in=validator_array).values("public_key", "activation_epoch", "validator_id")
    validator_dict = {v["validator_id"]: v for v in validators}

    sync_duty_count, sync_participation_count, active_sync_validators, next_sync_validators, total_attestations = \
        get_sync_attestation_dashboard_info(cached_validators, validator_array, current_slot, current_epoch, validator_update_slot, validator_dict)

    chart_data, apy, total_rewards = get_chart_data_daily_rewards(validator_array, timezone.now().date(), 30)
    
    context = {
        'validator_array': ','.join(map(str, validator_array)),
        'sync_duty_count': sync_duty_count,
        'validator_count': len(validator_array),
        'chart_data': json.dumps(chart_data),
    }
    view = render(request, 'frontend/sync_live_monitoring.html', context)

    return view


@measure_execution_time
def show_slot(request, slot_number):
    slot = get_object_or_404(Block, slot_number=slot_number)
    slot.timestamp = slot.timestamp.isoformat()
    slot.total_reward = float(slot.total_reward) / 10**18

    context = {
        'slot': slot,
    }
    view = render(request, 'frontend/slot.html', context)

    return view


@measure_execution_time
def show_epoch(request, epoch):
    epoch = get_object_or_404(Epoch, epoch=epoch)
    epoch.timestamp = epoch.timestamp.isoformat()

    context = {
        'epoch': epoch,
    }
    view = render(request, 'frontend/epoch.html', context)

    return view


@measure_execution_time
def settings(request):
    context = {
    }
    view = render(request, 'frontend/settings.html', context)

    return view


def handler404(request, exception):
    return render(request, 'frontend/404.html', status=404)
