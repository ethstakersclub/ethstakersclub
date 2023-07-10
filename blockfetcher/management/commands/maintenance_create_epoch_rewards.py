from django.core.management.base import BaseCommand
from blockfetcher.tasks import load_epoch_rewards


class Command(BaseCommand):
    help = 'Process the epoch rewards at the specified epoch'

    def add_arguments(self, parser):
        parser.add_argument('epoch', type=int, help='An integer parameter')

    def handle(self, *args, **options):
        epoch = options['epoch']

        load_epoch_rewards(epoch)