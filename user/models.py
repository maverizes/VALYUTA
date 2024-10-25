from typing import TYPE_CHECKING
from django.db import models

if TYPE_CHECKING:
    from currency.models import Currency

class User(models.Model):
    chat_id = models.CharField(max_length=64, primary_key=True)
    name = models.CharField(max_length=64)
    favourite_currency = models.ForeignKey(
        'currency.Currency', on_delete=models.SET_NULL, null=True, blank=True)
    username = models.CharField(max_length=64)
    phone_number = models.CharField(max_length=64)
    registered_at = models.DateTimeField(auto_now_add=True)
    change_currency = models.BooleanField(default=False)

    referrer = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name="referrals"
    ) 
    referral_count = models.IntegerField(default=0)  

    def __str__(self):
        return f"User: {self.name}"
