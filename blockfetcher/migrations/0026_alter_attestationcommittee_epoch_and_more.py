# Generated by Django 4.1.9 on 2023-05-23 13:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blockfetcher', '0025_attestationcommittee_blockfetche_validat_70f015_gin'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attestationcommittee',
            name='epoch',
            field=models.IntegerField(db_index=True),
        ),
        migrations.AlterField(
            model_name='attestationcommittee',
            name='index',
            field=models.IntegerField(),
        ),
    ]
