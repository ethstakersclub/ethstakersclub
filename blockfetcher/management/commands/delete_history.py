from django.core.management.base import BaseCommand
from blockfetcher.models import Main, Block, Validator, Withdrawal, AttestationCommittee, Epoch, ValidatorBalance


class Command(BaseCommand):
    help = 'Deletes all ValidatorBalance objects in the database'

    def handle(self, *args, **options):
        for i in range(0, ValidatorBalance.objects.all().count(), 10000):
            ValidatorBalance.objects.filter(pk__in=ValidatorBalance.objects.all().values_list('pk')[:10000]).delete()