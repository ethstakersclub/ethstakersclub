from django.contrib import admin
from .models import Withdrawal, StakingDeposit, Validator, Block, AttestationCommittee, Epoch, Main, ValidatorBalance, MissedAttestation, SyncCommittee, MissedSync


class StakingDepositAdmin(admin.ModelAdmin):
    raw_id_fields = ('validator',)

class WithdrawalAdmin(admin.ModelAdmin):
    raw_id_fields = ('block',)

admin.site.register(Block)
admin.site.register(Validator)
admin.site.register(AttestationCommittee)
admin.site.register(Epoch)
admin.site.register(Main)
admin.site.register(ValidatorBalance)
admin.site.register(MissedAttestation)
admin.site.register(SyncCommittee)
admin.site.register(MissedSync)
admin.site.register(StakingDeposit, StakingDepositAdmin)
admin.site.register(Withdrawal, WithdrawalAdmin)
