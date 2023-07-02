from django.core.management.base import BaseCommand
from blockfetcher.models import Main, Block, Validator, Withdrawal, AttestationCommittee, Epoch, ValidatorBalance, MissedAttestation, EpochReward


class Command(BaseCommand):
    help = 'Deletes all objects in the database'

    def handle(self, *args, **options):
        first = EpochReward.objects.order_by('pk').first().pk
        last = EpochReward.objects.order_by('pk').last().pk
        batch_size = 10000
        last_deleted = 0
        for i in range(first, last - batch_size, batch_size):
            EpochReward.objects.filter(pk__gte=i, pk__lte=i+batch_size).delete()
            last_deleted = i
        EpochReward.objects.filter(pk__gte=last_deleted, pk__lte=last).delete()
        
        '''
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
        '''
