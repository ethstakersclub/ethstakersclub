# Generated by Django 4.2.1 on 2023-05-30 18:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blockfetcher', '0049_alter_epochattestationreward_epoch_and_more'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='epochattestationreward',
            index_together=set(),
        ),
        migrations.AlterField(
            model_name='epochattestationreward',
            name='epoch',
            field=models.PositiveIntegerField(db_index=True),
        ),
    ]