from typing import TYPE_CHECKING
from django.db import models
from decimal import Decimal


if TYPE_CHECKING:
    from user.models import User
    from currency.models import Currency


class Conversion(models.Model):
    user: "User" = models.ForeignKey('user.User', on_delete=models.CASCADE)
    currency: "Currency" = models.ForeignKey('currency.Currency', on_delete=models.CASCADE)

    direction = models.CharField(choices=[
        ("FROM_UZS", "So'mdan"),
        ("TO_UZS", "So'mga")
    ], max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    convert_sum = models.DecimalField(max_digits=10, decimal_places=2)
    convert_date = models.DateTimeField(auto_now_add=True)
