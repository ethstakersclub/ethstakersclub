# Generated by Django 4.2.1 on 2023-06-23 22:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blockfetcher', '0082_epoch_active_validators_epoch_exited_validators_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='epoch',
            name='exiting_statuses',
            field=models.IntegerField(default=None, null=True),
        ),
    ]
