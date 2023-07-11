from django.core.management.base import BaseCommand
from ethstakersclub.settings import SLOTS_PER_EPOCH, GENESIS_TIMESTAMP, SECONDS_PER_SLOT
from blockfetcher.tasks import make_balance_snapshot
from django.utils import timezone
from datetime import datetime


class Command(BaseCommand):
    help = 'Run a balance snapshot on the defined slots'

    def add_arguments(self, parser):
        parser.add_argument('from_slot', type=int, help='An integer parameter')
        parser.add_argument('to_slot', type=int, help='An integer parameter')

    def handle(self, *args, **options):
        from_slot = options['from_slot']
        to_slot = options['to_slot']

        SNAPSHOT_CREATION_EPOCH_DELAY = 10

        last_balance_snapshot_planned_date = timezone.make_aware(datetime.fromtimestamp(0), timezone=timezone.utc).date()
        loop_epoch = 0

        for slot in range(from_slot, to_slot):
            if int(slot / SLOTS_PER_EPOCH) != loop_epoch:
                snapshot_creation_timestamp = GENESIS_TIMESTAMP + (SECONDS_PER_SLOT * (slot - (SLOTS_PER_EPOCH * SNAPSHOT_CREATION_EPOCH_DELAY)))
                snapshot_creation_date = timezone.make_aware(datetime.fromtimestamp(snapshot_creation_timestamp), timezone=timezone.utc)

                if last_balance_snapshot_planned_date < snapshot_creation_date.date():
                    print(f"snapshot task started {slot}")
                    make_balance_snapshot(slot, snapshot_creation_timestamp, True)
                    last_balance_snapshot_planned_date = snapshot_creation_date.date()

                loop_epoch = int(slot / SLOTS_PER_EPOCH)