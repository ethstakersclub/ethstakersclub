# Generated by Django 4.1.9 on 2023-05-20 19:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('blockfetcher', '0002_remove_block_slot_block_fee_recipient_block_proposer_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='block',
            name='proposer',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='blockfetcher.validator'),
        ),
    ]
