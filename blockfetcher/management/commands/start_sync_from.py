from django.core.management.base import BaseCommand
from blockfetcher.models import Main
from django.utils import timezone
from ethstakersclub.settings import SLOTS_PER_EPOCH, GENESIS_TIMESTAMP, SECONDS_PER_SLOT, MAX_SLOTS_PER_DAY
from datetime import datetime


class Command(BaseCommand):
    help = 'Set up initial sync starting from a specified slot'

    def add_arguments(self, parser):
        parser.add_argument('slot', type=int, help='The starting slot for initial sync')

    def handle(self, *args, **options):
        slot = options['slot']

        main_row, created = Main.objects.get_or_create(id=1, defaults={
            'last_balance_snapshot_planned_date': timezone.make_aware(datetime.fromtimestamp(GENESIS_TIMESTAMP + (SECONDS_PER_SLOT * (slot + MAX_SLOTS_PER_DAY))), timezone=timezone.utc),
            'finalized_checkpoint_epoch': 0,
            'justified_checkpoint_epoch': 0,
            'last_mev_reward_fetch_slot': slot,
            'last_slot': slot,
            'last_missed_attestation_aggregation_epoch': slot / SLOTS_PER_EPOCH,
        })

        if not created:
            self.stdout.write(self.style.WARNING("Main object already exists."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Main object at slot {slot} created."))