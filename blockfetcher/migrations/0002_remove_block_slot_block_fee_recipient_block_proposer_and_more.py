# Generated by Django 4.1.9 on 2023-05-20 19:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('blockfetcher', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='block',
            name='slot',
        ),
        migrations.AddField(
            model_name='block',
            name='fee_recipient',
            field=models.CharField(default='', max_length=64, unique=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='block',
            name='proposer',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='blockfetcher.validator'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='validator',
            name='total_withdrawn',
            field=models.DecimalField(decimal_places=0, default=0, max_digits=27),
        ),
        migrations.CreateModel(
            name='Withdrawal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=0, default=0, max_digits=27)),
                ('address', models.CharField(max_length=64)),
                ('index', models.IntegerField()),
                ('epoch_number', models.IntegerField()),
                ('validator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='blockfetcher.validator')),
            ],
        ),
    ]