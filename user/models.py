from typing import TYPE_CHECKING
from django.db import models

if TYPE_CHECKING:
    from currency.models import Currency
    from referral.models import Referral


class User(models.Model):
    chat_id = models.CharField(max_length=64, primary_key=True)
    name = models.CharField(max_length=64, null=True, blank=True)
    favourite_currency = models.ForeignKey(
        'currency.Currency', on_delete=models.SET_NULL, null=True, blank=True)
    username = models.CharField(max_length=64, null=True, blank=True)
    phone_number = models.CharField(max_length=64, null=True, blank=True)
    registered_at = models.DateTimeField(auto_now_add=True)
    change_currency = models.BooleanField(default=False)

    # referrer = models.ForeignKey(
    # 'self', on_delete=models.SET_NULL, null=True, blank=True, related_name="referrals"
    # )

    is_admin = models.BooleanField(default=False)

    referral: "Referral" = models.ForeignKey(
        'referral.Referral', on_delete=models.SET_NULL, null=True, blank=True, related_name="users")

    def __str__(self):
        return f"User: {self.name}"
