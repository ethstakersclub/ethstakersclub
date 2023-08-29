from django.core.management.base import BaseCommand
from ethstakersclub.settings import BEACON_API_ENDPOINT, BEACON_API_ENDPOINT_OPTIONAL_GZIP
from blockfetcher.models import Block, Withdrawal
from blockfetcher.beacon_api import BeaconAPI
import logging
import requests
import decimal

beacon = BeaconAPI(BEACON_API_ENDPOINT_OPTIONAL_GZIP)
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process the specified slot or a range of slots'

    def add_arguments(self, parser):
        parser.add_argument('slot1', type=int, help='An integer parameter for the starting slot')
        parser.add_argument('slot2', type=int, nargs='?', help='An integer parameter for the ending slot (optional)')

    def handle(self, *args, **options):
        slot1 = options['slot1']
        slot2 = options['slot2']

        existing_withdrawals = Withdrawal.objects.all().order_by("index").values_list("index", flat=True)
        prev = existing_withdrawals[0] - 1
        for e in existing_withdrawals:
            if e != prev + 1:
                print(f"{e} slot:{Withdrawal.objects.get(index=prev).block.slot_number}")
            prev = e
        
        if slot2 is None:
            self.process_slot(slot1)
        else:
            self.process_slot_range(slot1, slot2)

    def process_slot(self, slot):
        self.load_block(slot)
        self.stdout.write(self.style.SUCCESS(f'Started processing slot {slot}'))

    def process_slot_range(self, start_slot, end_slot):
        if start_slot > end_slot:
            self.stdout.write(self.style.ERROR('Error: Starting slot should be less than or equal to ending slot.'))
            return

        for slot in range(start_slot, end_slot + 1):
            self.process_slot(slot)

        self.stdout.write(self.style.SUCCESS(f'Started processing slots from {start_slot} to {end_slot}'))
    
    def load_block(self, slot):
        url = BEACON_API_ENDPOINT + "/eth/v1/beacon/blocks/" + str(slot)
        block = requests.get(url).json()
        logger.info("Process block at slot %s: %s", slot, str(block)[:200])

        block_not_found = "message" in block and str(block["message"]) == "NOT_FOUND: beacon block at slot " + str(slot)

        try:
            new_block = Block.objects.get(slot_number=int(slot))
        except:
            return

        if block_not_found:
            logger.info("block at slot " + str(slot) + " not found (likely not proposed)")
            return
        else:
            if "execution_payload" in block["data"]["message"]["body"]:
                if "withdrawals" in block["data"]["message"]["body"]["execution_payload"]:
                    existing_withdrawals = Withdrawal.objects.filter(block__slot_number=slot).values_list("index", flat=True)
                    print(existing_withdrawals)

                    withdrawals = block["data"]["message"]["body"]["execution_payload"]["withdrawals"]
                    withdrawal_objects = [
                        Withdrawal(
                            index=withdrawal["index"],
                            amount=decimal.Decimal(withdrawal["amount"]),
                            validator=int(withdrawal["validator_index"]),
                            address=withdrawal["address"],
                            block=new_block,
                        )
                        for withdrawal in withdrawals
                        if int(withdrawal["index"]) not in existing_withdrawals
                    ]
                    print(withdrawal_objects)
                    if len(withdrawal_objects) > 0:
                        logger.info("create missing withdrawals")
                        Withdrawal.objects.bulk_create(withdrawal_objects, update_conflicts=True, 
                                                        update_fields=["amount", "validator", "address", "block"], 
                                                        unique_fields=["index"])
