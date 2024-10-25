# Generated by Django 5.1.2 on 2024-10-25 16:07

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0004_rename_main_currency_user_favourite_currency'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='referral_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='user',
            name='referrer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='referrals', to='user.user'),
        ),
    ]
