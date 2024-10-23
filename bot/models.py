from django.db import models
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from user.models import User
    from currency.models import Currency


class User(models.Model):
    chat_id = models.BigIntegerField(primary_key=True, db_index=True)

    def __str__(self):
        return f"User: {self.chat_id}"


class Registration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=32)

    currency: "Currency" = models.ForeignKey(
        "currency.Currency", on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return f"{self.name} ({self.currency} - {self.phone_number})"
