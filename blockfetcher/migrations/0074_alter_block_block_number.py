# Generated by Django 4.2.1 on 2023-06-15 14:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blockfetcher', '0073_alter_epochattestationreward_validator_ids'),
    ]

    operations = [
        migrations.AlterField(
            model_name='block',
            name='block_number',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
