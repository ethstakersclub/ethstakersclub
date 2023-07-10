from django.core.management.base import BaseCommand
from blockfetcher.tasks import fetch_mev_rewards_task
import time


class Command(BaseCommand):
    help = 'Process the specified slot'

    def add_arguments(self, parser):
        parser.add_argument('from_slot', type=int, help='An integer parameter')
        parser.add_argument('to_slot', type=int, help='An integer parameter')

    def handle(self, *args, **options):
        from_slot = options['from_slot']
        to_slot = options['to_slot']

        for i in range(from_slot, to_slot, 1000):
            task = fetch_mev_rewards_task.delay(i, i + 1000)

            while not task.ready():
                time.sleep(1)
            
            time.sleep(10)