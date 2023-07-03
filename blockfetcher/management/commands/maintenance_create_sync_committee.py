from django.core.management.base import BaseCommand
from blockfetcher.management.commands.block_listener import create_sync_committee


class Command(BaseCommand):
    help = 'Process the specified sync committee at a epoch'

    def add_arguments(self, parser):
        parser.add_argument('epoch', type=int, help='An integer parameter')

    def handle(self, *args, **options):
        epoch = options['epoch']

        create_sync_committee(epoch)