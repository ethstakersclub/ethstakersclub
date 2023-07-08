# context_processors.py

from ethstakersclub.settings import CURRENCY_NAME, VALIDATOR_MONITORING_LIMIT, DEBUG
from blockfetcher.cache import *
from blockfetcher.models import Main

def general_context_processor(request):
    current_epoch = get_current_epoch_from_cache()
    current_slot = get_current_slot_from_cache()
    finalized_epoch = Main.objects.get(id=1).finalized_checkpoint_epoch

    return {
        'DEBUG': DEBUG,
        'currency_name': CURRENCY_NAME,
        'validator_monitoring_limit': VALIDATOR_MONITORING_LIMIT,
        'current_slot': current_slot,
        'current_epoch': current_epoch,
        'finalized_epoch': finalized_epoch,
        }