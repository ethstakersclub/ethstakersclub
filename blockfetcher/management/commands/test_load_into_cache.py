from django.core.management.base import BaseCommand
from blockfetcher.task_process_validators import process_validators
from ethstakersclub.settings import BEACON_API_ENDPOINT, SLOTS_PER_EPOCH
import requests
from django.core.cache import cache


class Command(BaseCommand):
    help = 'Loads all required items into the cache'

    def handle(self, *args, **options):
        url = BEACON_API_ENDPOINT + "/eth/v1/beacon/blocks/head"
        head = requests.get(url).json()
        head_slot = int(head["data"]["message"]["slot"])
        head_epoch = int(head_slot / SLOTS_PER_EPOCH)

        cache.set("head_slot", head_slot, timeout=10000)
        cache.set("head_epoch", head_epoch, timeout=10000)

        process_validators(head_slot)