# Generated by Django 4.2.1 on 2023-07-02 08:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blockfetcher', '0093_alter_epochreward_attestation_head_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='block',
            name='attestation_count',
        ),
        migrations.RemoveField(
            model_name='block',
            name='participation_rate',
        ),
        migrations.RemoveField(
            model_name='block',
            name='sync_missed',
        ),
        migrations.RemoveField(
            model_name='block',
            name='validator_count',
        ),
    ]
