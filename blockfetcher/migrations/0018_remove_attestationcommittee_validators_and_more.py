# Generated by Django 4.1.9 on 2023-05-21 17:46

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blockfetcher', '0017_attestationcommittee_epoch'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='attestationcommittee',
            name='validators',
        ),
        migrations.AddField(
            model_name='attestationcommittee',
            name='validator_ids',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(), default=[], size=None),
            preserve_default=False,
        ),
    ]