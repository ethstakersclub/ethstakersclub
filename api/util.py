from functools import wraps
import time


def calculate_activation_epoch(validators_ahead ,validator_update_epoch, validators_per_epoch, status, activation_epoch):
    if status == "pending_initialized":
        return "pending"
    elif validators_ahead == -1 and activation_epoch != 18446744073709551615:
        return activation_epoch
    if validators_ahead < 0:
        validators_ahead = 0
    return validator_update_epoch + int(validators_ahead / validators_per_epoch) + 1


def measure_execution_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        print(f"Execution time for {func.__name__}: {execution_time} seconds")
        return result
    return wrapper