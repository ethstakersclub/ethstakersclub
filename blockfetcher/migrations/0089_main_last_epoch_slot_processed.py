# Generated by Django 4.2.1 on 2023-07-01 03:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blockfetcher', '0088_alter_epoch_validators_status_json'),
    ]

    operations = [
        migrations.AddField(
            model_name='main',
            name='last_epoch_slot_processed',
            field=models.IntegerField(default=0),
        ),
    ]
