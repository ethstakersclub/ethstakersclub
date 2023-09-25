from django.core.management.base import BaseCommand
from blockfetcher.tasks import calc_highest_rewards_task
from blockfetcher.cache import get_current_slot_from_cache
import time


class Command(BaseCommand):
    help = 'Process the specified slot'

    def handle(self, *args, **options):
        task = calc_highest_rewards_task.delay(get_current_slot_from_cache())

        while not task.ready():
            time.sleep(1)
            