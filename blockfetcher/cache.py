from django.core.cache import cache
import json


def get_validator_from_cache(index):
    try:
        data = cache.get('validator_' + str(index))
        return json.loads(data)
    except:
        return{}
    

def get_validators_from_cache(index_array):
    cache_keys = [f'validator_{index}' for index in index_array]
    data = cache.get_many(cache_keys)

    return [json.loads(value) for value in data.values()]


def get_rewards_and_penalties_from_cache(index_array, epoch):
    cache_keys = [f"reward_{epoch}:{index}" for index in index_array]
    data = cache.get_many(cache_keys)

    return [value for value in data.values() if value is not None]


def get_active_validators_count_from_cache():
    try:
        return int(cache.get('active_validators'))
    except:
        return 0


def get_current_epoch_from_cache():
    try:
        return int(cache.get('head_epoch'))
    except:
        return 0


def get_current_slot_from_cache():
    try:
        return int(cache.get('head_slot'))
    except:
        return 0


def get_validator_update_slot_from_cache():
    try:
        return int(cache.get('validator_update_slot'))
    except:
        return 0


def get_average_attestation_efficiency_from_cache():
    try:
        return int(cache.get('average_attestation_efficiency'))
    except:
        return 0
    

def get_latest_rewards_and_penalties_epoch():
    try:
        return int(cache.get('latest_rewards_and_penalties_epoch'))
    except:
        return 0