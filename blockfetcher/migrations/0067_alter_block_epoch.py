# Generated by Django 4.2.1 on 2023-06-07 00:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blockfetcher', '0066_alter_missedattestation_slot_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='block',
            name='epoch',
            field=models.PositiveIntegerField(),
        ),
    ]
