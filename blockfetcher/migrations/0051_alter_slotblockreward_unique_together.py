# Generated by Django 4.2.1 on 2023-05-30 18:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blockfetcher', '0050_alter_epochattestationreward_index_together_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='slotblockreward',
            unique_together={('block', 'validator_id')},
        ),
    ]
