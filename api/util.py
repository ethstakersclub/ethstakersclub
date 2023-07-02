def calculate_activation_epoch(validators_ahead ,validator_update_epoch, validators_per_epoch, status, activation_epoch):
    if status == "pending_initialized":
        return "pending"
    elif validators_ahead == -1 and activation_epoch != 18446744073709551615:
        return activation_epoch
    if validators_ahead < 0:
        validators_ahead = 0
    return validator_update_epoch + int(validators_ahead / validators_per_epoch) + 1