from django.core.management.base import BaseCommand
from blockfetcher.models import Withdrawal


class Command(BaseCommand):
    help = 'Process the specified slot'

    def handle(self, *args, **options):
        count = 0
        lastSeenId = float('-Inf')
        rows = Withdrawal.objects.all().order_by('index')

        for row in rows:
            if count % 2000 == 0:
                print(f"rows checked: {count}")
            if row.index == lastSeenId:
                row.delete()
            else:
                lastSeenId = row.index
            count += 1
