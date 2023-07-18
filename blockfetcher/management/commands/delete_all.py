from django.core.management.base import BaseCommand
from blockfetcher.models import Main, Block, Validator, Withdrawal, AttestationCommittee, Epoch, ValidatorBalance, MissedAttestation


class Command(BaseCommand):
    help = 'Deletes all objects in the database'

    def handle(self, *args, **options):
        Withdrawal.objects.all().delete()
        for i in range(0, Block.objects.all().count(), 10000):
            Block.objects.filter(pk__in=Block.objects.all().values_list('pk')[:10000]).delete()
        for i in range(0, AttestationCommittee.objects.all().count(), 10000):
            AttestationCommittee.objects.all().delete()
        Epoch.objects.all().delete()
        for i in range(0, ValidatorBalance.objects.all().count(), 10000):
            ValidatorBalance.objects.filter(pk__in=ValidatorBalance.objects.all().values_list('pk')[:10000]).delete()
        for i in range(0, MissedAttestation.objects.all().count(), 10000):
            MissedAttestation.objects.filter(pk__in=MissedAttestation.objects.all().values_list('pk')[:10000]).delete()
