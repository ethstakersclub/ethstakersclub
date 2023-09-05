# context_processors.py

from ethstakersclub.settings import CURRENCY_NAME, VALIDATOR_MONITORING_LIMIT, DEBUG, ATTESTATION_EFFICIENCY_EPOCHS, EPOCH_REWARDS_HISTORY_DISTANCE, \
                                    ACTIVE_STATUSES, PENDING_STATUSES, EXITED_STATUSES, EXITING_STATUSES, CURRENCY_NAME_FULL, VALIDATOR_MONITORING_LIMIT_MAX
from blockfetcher.cache import *
from blockfetcher.models import Main

def general_context_processor(request):
    current_epoch = get_current_epoch_from_cache()
    current_slot = get_current_slot_from_cache()
    finalized_epoch = Main.objects.get(id=1).finalized_checkpoint_epoch

    return {
        'DEBUG': DEBUG,
        'currency_name': CURRENCY_NAME,
        'currency_name_full': CURRENCY_NAME_FULL,
        'attestation_efficiency_epochs': ATTESTATION_EFFICIENCY_EPOCHS,
        'validator_monitoring_limit': VALIDATOR_MONITORING_LIMIT,
        'validator_monitoring_limit_max': VALIDATOR_MONITORING_LIMIT_MAX,
        'epoch_rewards_history_distance': EPOCH_REWARDS_HISTORY_DISTANCE,
        'active_statuses': json.dumps(list(ACTIVE_STATUSES)),
        'pending_statuses': json.dumps(list(PENDING_STATUSES)),
        'exited_statuses': json.dumps(list(EXITED_STATUSES)),
        'exiting_statuses': json.dumps(list(EXITING_STATUSES)),
        'current_slot': current_slot,
        'current_epoch': current_epoch,
        'finalized_epoch': finalized_epoch,
        }