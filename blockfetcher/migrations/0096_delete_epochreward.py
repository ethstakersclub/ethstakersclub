# Generated by Django 4.2.1 on 2023-07-17 20:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blockfetcher', '0095_remove_synccommittee_missed_remove_withdrawal_id_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='EpochReward',
        ),
    ]
