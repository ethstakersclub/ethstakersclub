# Generated by Django 4.2.1 on 2023-07-01 07:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blockfetcher', '0089_main_last_epoch_slot_processed'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='attestation',
            name='block_added',
        ),
        migrations.RemoveField(
            model_name='attestation',
            name='block_attesting',
        ),
        migrations.AlterUniqueTogether(
            name='epochattestationreward',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='epochattestationreward',
            name='validators',
        ),
        migrations.DeleteModel(
            name='EpochSyncReward',
        ),
        migrations.RemoveField(
            model_name='proposerduty',
            name='validator',
        ),
        migrations.AlterUniqueTogether(
            name='slotblockreward',
            unique_together=None,
        ),
        migrations.AlterIndexTogether(
            name='slotblockreward',
            index_together=None,
        ),
        migrations.RemoveField(
            model_name='slotblockreward',
            name='block',
        ),
        migrations.RemoveField(
            model_name='main',
            name='genesis_time',
        ),
        migrations.DeleteModel(
            name='Attestation',
        ),
        migrations.DeleteModel(
            name='EpochAttestationReward',
        ),
        migrations.DeleteModel(
            name='ProposerDuty',
        ),
        migrations.DeleteModel(
            name='SlotBlockReward',
        ),
    ]
