# Generated by Django 4.1.9 on 2023-05-22 13:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('blockfetcher', '0020_alter_block_epoch_alter_block_slot_number'),
    ]

    operations = [
        migrations.CreateModel(
            name='Epoch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dependent_root', models.CharField(max_length=68, unique=True)),
                ('epoch', models.IntegerField(unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='ProposerDuty',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('epoch', models.IntegerField()),
                ('slot', models.IntegerField(unique=True)),
                ('validator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='blockfetcher.validator')),
            ],
        ),
    ]
