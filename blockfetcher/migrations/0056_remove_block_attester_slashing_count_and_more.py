# Generated by Django 4.2.1 on 2023-06-02 19:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blockfetcher', '0055_main_last_missed_attestation_aggregation_epoch_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='block',
            name='attester_slashing_count',
        ),
        migrations.RemoveField(
            model_name='block',
            name='balance_churn',
        ),
        migrations.RemoveField(
            model_name='block',
            name='proposer_slashing_count',
        ),
        migrations.RemoveField(
            model_name='block',
            name='sync_aggregation',
        ),
        migrations.AddField(
            model_name='block',
            name='block_root',
            field=models.CharField(blank=True, max_length=66, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='block',
            name='graffiti',
            field=models.CharField(default='', max_length=66),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='block',
            name='parent_root',
            field=models.CharField(blank=True, max_length=66, null=True),
        ),
        migrations.AddField(
            model_name='block',
            name='randao_reveal',
            field=models.CharField(default='', max_length=194),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='block',
            name='signature',
            field=models.CharField(default='', max_length=194),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='block',
            name='state_root',
            field=models.CharField(blank=True, max_length=66, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='block',
            name='sync_committee_bits',
            field=models.CharField(default='', max_length=130),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='block',
            name='sync_committee_signature',
            field=models.CharField(default='', max_length=194),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='MissedSync',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('period', models.IntegerField()),
                ('slot', models.IntegerField(db_index=True)),
                ('validator_id', models.PositiveIntegerField(db_index=True)),
            ],
            options={
                'unique_together': {('slot', 'validator_id')},
                'index_together': {('validator_id', 'slot')},
            },
        ),
    ]
