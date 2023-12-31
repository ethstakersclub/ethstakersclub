# Generated by Django 4.1.9 on 2023-05-20 19:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blockfetcher', '0003_alter_block_proposer'),
    ]

    operations = [
        migrations.AlterField(
            model_name='block',
            name='attestation_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='block',
            name='attester_slashing_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='block',
            name='balance_churn',
            field=models.DecimalField(decimal_places=9, default=0, max_digits=20),
        ),
        migrations.AlterField(
            model_name='block',
            name='block_hash',
            field=models.CharField(max_length=66, unique=True),
        ),
        migrations.AlterField(
            model_name='block',
            name='block_transfer_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='block',
            name='deposit_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='block',
            name='fee_recipient',
            field=models.CharField(max_length=66, unique=True),
        ),
        migrations.AlterField(
            model_name='block',
            name='parent_hash',
            field=models.CharField(max_length=66),
        ),
        migrations.AlterField(
            model_name='block',
            name='participation_rate',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
        migrations.AlterField(
            model_name='block',
            name='proposer_slashing_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='block',
            name='timestamp',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='block',
            name='validator_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='block',
            name='voluntary_exit_count',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
