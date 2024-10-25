from django.db import models

class Currency(models.Model):
    name = models.CharField(max_length=64)
    currency_code = models.CharField(max_length=8, unique=True) 
    cb_price = models.DecimalField(max_digits=10, decimal_places=2)  

    def __str__(self):
        return f"{self.name} ({self.currency_code})"
