from django.core.management.base import BaseCommand
from blockfetcher.tasks import load_block_task
from ethstakersclub.settings import SLOTS_PER_EPOCH


class Command(BaseCommand):
    help = 'Process the specified slot'

    def add_arguments(self, parser):
        parser.add_argument('slot', type=int, help='An integer parameter')

    def handle(self, *args, **options):
        slot = options['slot']

        load_block_task.delay(slot, slot / SLOTS_PER_EPOCH)