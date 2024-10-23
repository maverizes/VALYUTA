# Generated by Django 5.1.2 on 2024-10-21 13:27

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('conversion', '0001_initial'),
        ('currency', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='conversion',
            name='from_currency',
        ),
        migrations.RemoveField(
            model_name='conversion',
            name='to_currency',
        ),
        migrations.AddField(
            model_name='conversion',
            name='currency',
            field=models.ForeignKey(default=2024, on_delete=django.db.models.deletion.CASCADE, related_name='currency', to='currency.currency'),
            preserve_default=False,
        ),
    ]