from django.core.management.base import BaseCommand
from blockfetcher.tasks import load_epoch_task
from ethstakersclub.settings import SLOTS_PER_EPOCH


class Command(BaseCommand):
    help = 'Process the specified epoch'

    def add_arguments(self, parser):
        parser.add_argument('epoch', type=int, help='An integer parameter')

    def handle(self, *args, **options):
        epoch = options['epoch']

        load_epoch_task.delay(epoch, epoch * SLOTS_PER_EPOCH)
