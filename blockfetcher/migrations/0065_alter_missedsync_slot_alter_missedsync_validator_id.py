# Generated by Django 4.2.1 on 2023-06-07 00:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blockfetcher', '0064_main_last_mev_reward_fetch_slot'),
    ]

    operations = [
        migrations.AlterField(
            model_name='missedsync',
            name='slot',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='missedsync',
            name='validator_id',
            field=models.PositiveIntegerField(),
        ),
    ]
