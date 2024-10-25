# Generated by Django 5.1.2 on 2024-10-23 06:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('currency', '0004_remove_currency_rate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='currency',
            name='cb_price',
            field=models.DecimalField(decimal_places=2, max_digits=5),
        ),
        migrations.AlterField(
            model_name='currency',
            name='currency_code',
            field=models.CharField(max_length=3),
        ),
    ]
