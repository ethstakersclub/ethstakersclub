from django.core.cache import cache
import json


def get_validator_from_cache(index):
    try:
        data = cache.get('validator_' + str(index))
        return json.loads(data.replace("'", "\""))
    except:
        return{}
    

def get_validators_from_cache(index_array):
    cache_keys = [f'validator_{index}' for index in index_array]
    data = cache.get_many(cache_keys)
    validators = []
    for value in data.values():
        validators.append(json.loads(value.replace("'", "\"")))
    return validators


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