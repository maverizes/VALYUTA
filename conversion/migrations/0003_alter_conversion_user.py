# Generated by Django 5.1.2 on 2024-10-22 08:01

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0001_initial'),
        ('conversion', '0002_remove_conversion_from_currency_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='conversion',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bot.user'),
        ),
    ]
