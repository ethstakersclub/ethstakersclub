# Generated by Django 4.1.9 on 2023-05-21 17:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blockfetcher', '0016_alter_attestationcommittee_slot'),
    ]

    operations = [
        migrations.AddField(
            model_name='attestationcommittee',
            name='epoch',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]