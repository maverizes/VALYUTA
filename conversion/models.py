from typing import TYPE_CHECKING
from django.db import models
from decimal import Decimal


if TYPE_CHECKING:
    from user.models import User
    from currency.models import Currency


class Conversion(models.Model):
    user = models.ForeignKey("user.User", on_delete=models.CASCADE)  # Use "user.User" (app_name.ModelName)
    currency = models.ForeignKey("currency.Currency", on_delete=models.CASCADE)  # String reference for Currency
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    convert_sum = models.DecimalField(max_digits=10, decimal_places=2)
    convert_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.name} converted {self.amount} from {self.currency.currency_code} to {self.convert_sum}"
