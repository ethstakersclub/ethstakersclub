from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex, OpClass, GistIndex
from django.db.models import Index
from django.db.models.functions import Lower


class Validator(models.Model):
    # Validator ID
    validator_id = models.IntegerField(unique=True, db_index=True, primary_key=True)

    # Validator public key
    public_key = models.CharField(max_length=98, unique=True, db_index=True)

    # Validator withdrawal credentials
    withdrawal_credentials = models.CharField(max_length=66)

    # Validator withdrawal address type - 0 or 1
    withdrawal_type = models.IntegerField(default=0)

    # Validator balance
    balance = models.DecimalField(max_digits=27, decimal_places=0, default=0)

    # Validator total withdrawn
    total_withdrawn = models.DecimalField(max_digits=27, decimal_places=0, default=0)

    # Validator effective balance
    # effective_balance = models.DecimalField(max_digits=27, decimal_places=0, default=0)

    # Validator status
    STATUS_CHOICES = [
        ('pending_initialized', 'Pending Initialized'),
        ('pending_queued', 'Pending Queued'),
        ('active_ongoing', 'Active Ongoing'),
        ('active_exiting', 'Active Exiting'),
        ('active_slashed', 'Active Slashed'),
        ('exited_unslashed', 'Exited Unslashed'),
        ('exited_slashed', 'Exited Slashed'),
        ('withdrawal_possible', 'Withdrawal Possible'),
        ('withdrawal_done', 'Withdrawal Done'),
        ('active', 'Active'),
        ('pending', 'Pending'),
        ('exited', 'Exited'),
        ('withdrawal', 'Withdrawal'),
        ('unknown', 'Unknown'),
    ]
    status = models.CharField(max_length=19, choices=STATUS_CHOICES, default="unknown")

    # Validator performance metrics
    # performance = models.IntegerField(default=0)

    # Validator creation date
    # created_at = models.DateTimeField(auto_now_add=True)

    # Last update date
    # updated_at = models.DateTimeField(auto_now=True)

    # Slashed
    active = models.BooleanField(default=True)

    # Activation epoch
    activation_epoch = models.DecimalField(max_digits=20, decimal_places=0, default=0)

    # Activation eligibility epoch
    activation_eligibility_epoch = models.DecimalField(max_digits=20, decimal_places=0, default=0)

    # Exit epoch
    exit_epoch = models.DecimalField(max_digits=20, decimal_places=0, default=0)

    # Withdrawable epoch
    withdrawable_epoch = models.DecimalField(max_digits=20, decimal_places=0, default=0)

    def __str__(self):
        return str(self.validator_id)


class Block(models.Model):
    # Proposer
    #proposer = models.ForeignKey(Validator, on_delete=models.CASCADE, null=True)
    proposer = models.PositiveIntegerField(blank=True, null=True, db_index=True)

    # Block number
    block_number = models.PositiveIntegerField(blank=True, null=True)

    # Slot number
    slot_number = models.PositiveIntegerField(unique=True, db_index=True, primary_key=True)

    # Block hash
    block_hash = models.CharField(max_length=66, unique=True, blank=True, null=True)

    # Parent root
    parent_root = models.CharField(max_length=66, blank=True, null=True)

    # Parent root
    state_root = models.CharField(max_length=66, unique=True, blank=True, null=True)

    # Block root
    block_root = models.CharField(max_length=66, unique=True, blank=True, null=True)

    # Fee recipient
    fee_recipient = models.CharField(max_length=66)

    # Timestamp
    timestamp = models.DateTimeField(null=True, blank=True)

    # Parent block hash
    parent_hash = models.CharField(max_length=84)

    # Validator count
    validator_count = models.PositiveIntegerField(default=0) # ----------

    # Beacon chain epoch
    epoch = models.PositiveIntegerField()

    # Validator participation rate
    participation_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0) # ----------

    # Number of attestations
    attestation_count = models.PositiveIntegerField(default=0) # ----------

    # Number of deposits
    deposit_count = models.PositiveIntegerField(default=0)

    # Number of voluntary exits
    voluntary_exit_count = models.PositiveIntegerField(default=0)

    # Number of block transfers
    block_transfer_count = models.PositiveIntegerField(default=0)

    # Total block reward
    total_reward = models.DecimalField(max_digits=27, decimal_places=0, default=0)

    # Mev Boost reward
    mev_reward = models.DecimalField(max_digits=27, decimal_places=0, default=0)

    # Total fees paid to proposer
    fee_reward = models.DecimalField(max_digits=27, decimal_places=0, default=0)

    # MEV boost relay used
    mev_boost_relay = ArrayField(models.CharField(max_length=25), null=True, blank=True)

    # MEV fee recipient
    mev_reward_recipient = models.CharField(max_length=66)

    # Total burnt fees
    burnt_fee = models.DecimalField(max_digits=27, decimal_places=0, default=0)

    # Total Transaction fees
    total_tx_fee = models.DecimalField(max_digits=27, decimal_places=0, default=0)

    # Transaction count
    transaction_count = models.IntegerField(default=0)

    # Sync committee aggregation
    sync_committee_bits = models.CharField(max_length=130)

    # Validators that missed the sync committee
    sync_missed = ArrayField(models.IntegerField(), null=True, blank=True) # ----------

    # Sync committee signature
    sync_committee_signature = models.CharField(max_length=194)

    # Randao reveal
    randao_reveal = models.CharField(max_length=194)

    # Graffiti
    graffiti = models.CharField(max_length=66)

    # Signature
    signature = models.CharField(max_length=194)

    # Has the block been orphaned(2),is it empty(1) or hasn't been processed yet(3)
    empty = models.IntegerField(default=3, db_index=True)

    def __str__(self):
        return f"Block #{self.slot_number}"


class Main(models.Model):
    last_slot = models.IntegerField(default=0)
    #last_checked_epoch = models.IntegerField(default=0)
    #last_balance_snapshot_date = models.DateField()
    last_balance_snapshot_planned_date = models.DateField()
    last_staking_deposits_update_block = models.IntegerField(default=0)
    last_epoch_slot_processed = models.IntegerField(default=0)

    last_missed_attestation_aggregation_epoch = models.IntegerField(default=0)
    last_mev_reward_fetch_slot = models.IntegerField(default=0)

    finalized_checkpoint_epoch = models.PositiveIntegerField()
    finalized_checkpoint_root = models.CharField(max_length=68)

    justified_checkpoint_epoch = models.PositiveIntegerField()
    justified_checkpoint_root = models.CharField(max_length=68)


class Withdrawal(models.Model):
    amount = models.DecimalField(max_digits=27, decimal_places=0, default=0)
    validator = models.IntegerField(db_index=True)
    address = models.CharField(max_length=64)
    index = models.IntegerField()
    block = models.ForeignKey(Block, on_delete=models.CASCADE, null=True)


class AttestationCommittee(models.Model):
    slot = models.IntegerField(db_index=True)
    validator_ids = ArrayField(models.IntegerField())
    distance = ArrayField(models.IntegerField())
    index = models.IntegerField()
    epoch = models.IntegerField()
    missed_attestation = ArrayField(models.IntegerField(), null=True, blank=True, default=None)

    class Meta:
        unique_together = [["slot", "index"]]
        #indexes = [
        #    GistIndex(fields=['validator_ids'], name="validator_ids_gist_idx", fillfactor=60, opclasses=['gist__intbig_ops'])
        #]

    #class Meta:
    #    indexes = [
    #        GinIndex(fields=['validator_ids']),
    #    ]


class StakingDeposit(models.Model):
    index = models.IntegerField(primary_key=True)
    block_number = models.IntegerField()
    amount = models.DecimalField(max_digits=27, decimal_places=0, default=0)
    public_key = models.CharField(max_length=98, db_index=True)
    withdrawal_credentials = models.CharField(max_length=66)
    signature = models.CharField(max_length=194)
    transaction_index = models.IntegerField()
    transaction_hash = models.CharField(max_length=66)
    validator = models.ForeignKey(Validator, on_delete=models.CASCADE, null=True, default=None)


class MissedAttestation(models.Model):
    slot = models.IntegerField()
    index = models.IntegerField()
    epoch = models.IntegerField()
    validator_id = models.PositiveIntegerField()

    class Meta:
        unique_together = [["slot", "index", "validator_id"]]
        index_together = [
            ["validator_id", "slot"],
        ]


class Epoch(models.Model):
    epoch = models.IntegerField(primary_key=True)
    dependent_root = models.CharField(max_length=68)
    timestamp = models.DateTimeField(null=True, blank=True)

    missed_attestation_count = models.IntegerField(default=None, null=True)
    total_attestations = models.IntegerField(default=None, null=True)
    participation_percent = models.FloatField(default=None, null=True)

    epoch_total_proposed_blocks = models.IntegerField(default=None, null=True)
    average_block_reward = models.DecimalField(max_digits=27, decimal_places=0, default=None, null=True)
    highest_block_reward = models.DecimalField(max_digits=27, decimal_places=0, default=None, null=True)

    active_validators = models.IntegerField(default=None, null=True)
    exited_validators = models.IntegerField(default=None, null=True)
    pending_validators = models.IntegerField(default=None, null=True)
    exiting_validators = models.IntegerField(default=None, null=True)
    validators_status_json = models.JSONField(null=True)


class ValidatorBalance(models.Model):
    validator_id = models.IntegerField(db_index=True)
    balance = models.DecimalField(max_digits=27, decimal_places=0, default=0)
    date = models.DateField(db_index=True)
    slot = models.IntegerField()
    total_consensus_balance = models.DecimalField(max_digits=27, decimal_places=0, default=0)
    execution_reward = models.DecimalField(max_digits=27, decimal_places=0, default=0)
    missed_attestations = models.IntegerField()
    missed_sync = models.IntegerField()

    class Meta:
        unique_together = [["validator_id", "date"]]


class EpochReward(models.Model):
    validator_id = models.PositiveIntegerField(db_index=True)
    epoch = models.PositiveIntegerField(db_index=True)

    attestation_head = models.DecimalField(max_digits=27, decimal_places=0, default=0)
    attestation_target = models.DecimalField(max_digits=27, decimal_places=0, default=0)
    attestation_source = models.DecimalField(max_digits=27, decimal_places=0, default=0)

    sync_reward = models.DecimalField(max_digits=27, decimal_places=0, null=True)
    sync_penalty = models.DecimalField(max_digits=27, decimal_places=0, null=True)

    block_attestations = models.DecimalField(max_digits=27, decimal_places=0, null=True)
    block_sync_aggregate = models.DecimalField(max_digits=27, decimal_places=0, null=True)
    block_proposer_slashings = models.DecimalField(max_digits=27, decimal_places=0, null=True)
    block_attester_slashings = models.DecimalField(max_digits=27, decimal_places=0, null=True)

    class Meta:
        unique_together = [["epoch", "validator_id"]]


class SyncCommittee(models.Model):
    period = models.IntegerField(db_index=True, unique=True)
    validator_ids = ArrayField(models.IntegerField(), null=True, blank=True)
    missed = ArrayField(models.IntegerField(), null=True, blank=True)

    class Meta:
        indexes = [
            GinIndex(fields=['validator_ids']),
        ]


class MissedSync(models.Model):
    period = models.IntegerField()
    slot = models.IntegerField()
    validator_id = models.PositiveIntegerField()

    class Meta:
        unique_together = [["slot", "validator_id"]]
        index_together = [
            ["validator_id", "slot"],
        ]