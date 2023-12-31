# Generated by Django 4.2.1 on 2023-06-18 12:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blockfetcher', '0075_alter_block_empty'),
    ]

    operations = [
        migrations.CreateModel(
            name='EpochReward',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('validator_id', models.PositiveIntegerField()),
                ('epoch', models.PositiveIntegerField()),
                ('attestation_head', models.DecimalField(decimal_places=0, default=0, max_digits=27)),
                ('attestation_target', models.DecimalField(decimal_places=0, default=0, max_digits=27)),
                ('attestation_source', models.DecimalField(decimal_places=0, default=0, max_digits=27)),
                ('sync_reward', models.DecimalField(decimal_places=0, max_digits=27, null=True)),
                ('sync_penalty', models.DecimalField(decimal_places=0, max_digits=27, null=True)),
                ('block_attestations', models.DecimalField(decimal_places=0, max_digits=27, null=True)),
                ('block_sync_aggregate', models.DecimalField(decimal_places=0, max_digits=27, null=True)),
                ('block_proposer_slashings', models.DecimalField(decimal_places=0, max_digits=27, null=True)),
                ('block_attester_slashings', models.DecimalField(decimal_places=0, max_digits=27, null=True)),
            ],
            options={
                'unique_together': {('epoch', 'validator_id')},
                'index_together': {('epoch', 'validator_id')},
            },
        ),
    ]
