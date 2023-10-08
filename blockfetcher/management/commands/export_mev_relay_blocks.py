from django.core.management.base import BaseCommand
from blockfetcher.models import Block, Validator
from django.db.models import Count
import re
import json


class Command(BaseCommand):
    help = 'Backup/Export all blocks of a MEV relay'

    def add_arguments(self, parser):
        parser.add_argument('relay', type=str, help='An string parameter')

    def handle(self, *args, **options):
        relay = str(options['relay'])

        blocks = Block.objects.filter(mev_boost_relay__contains=[relay])

        print(f"There are {blocks.count()} blocks from this relay.")

        # Query Validator to fetch all relevant validator_id values
        proposer_ids = list(blocks.values_list('proposer', flat=True))
        validators = Validator.objects.filter(validator_id__in=proposer_ids)

        # Create a dictionary for fast lookup of validator_id values
        validator_id_map = {validator.validator_id: validator for validator in validators}

        result_json = []
        count_unique = 0
        for block in blocks:
            if len(block.mev_boost_relay) == 1:
                count_unique += 1

            validator = validator_id_map.get(block.proposer)
            if validator:
                result_json.append({
                    "slot": block.slot_number,
                    "parent_hash": block.parent_hash,
                    "block_hash": block.block_hash,
                    "builder_pubkey": validator.public_key,
                    "builder_id": block.proposer,
                    "proposer_fee_recipient": block.mev_reward_recipient,
                    "value": int(block.mev_reward),
                    "num_tx": int(block.transaction_count),
                    "block_number": block.block_number,
                    "timestamp": str(block.timestamp),
                    "mev_boost_relay": block.mev_boost_relay,
                })
        
        print(f"There are {count_unique} blocks unique to this relay.")
        
        # Generate the output file name
        relay_name = relay.lower().replace(' ', '_')
        output_file_name = f'result_{relay_name}.json'

        # Write result_json to a JSON file
        with open(output_file_name, 'w') as file:
            json.dump(result_json, file, indent=4)

        self.stdout.write(self.style.SUCCESS(f"Result JSON written to '{output_file_name}'."))
