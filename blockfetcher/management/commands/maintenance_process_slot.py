from django.core.management.base import BaseCommand
from blockfetcher.tasks import load_block_task
from ethstakersclub.settings import SLOTS_PER_EPOCH


class Command(BaseCommand):
    help = 'Process the specified slot or a range of slots'

    def add_arguments(self, parser):
        parser.add_argument('slot1', type=int, help='An integer parameter for the starting slot')
        parser.add_argument('slot2', type=int, nargs='?', help='An integer parameter for the ending slot (optional)')

    def handle(self, *args, **options):
        slot1 = options['slot1']
        slot2 = options['slot2']

        if slot2 is None:
            # Only process the specified single slot
            self.process_slot(slot1)
        else:
            # Process the range of slots
            self.process_slot_range(slot1, slot2)

    def process_slot(self, slot):
        load_block_task.delay(slot, slot / SLOTS_PER_EPOCH)
        self.stdout.write(self.style.SUCCESS(f'Started processing slot {slot}'))

    def process_slot_range(self, start_slot, end_slot):
        if start_slot > end_slot:
            self.stdout.write(self.style.ERROR('Error: Starting slot should be less than or equal to ending slot.'))
            return

        for slot in range(start_slot, end_slot + 1):
            self.process_slot(slot)

        self.stdout.write(self.style.SUCCESS(f'Started processing slots from {start_slot} to {end_slot}'))