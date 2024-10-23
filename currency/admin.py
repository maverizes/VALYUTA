from django.contrib import admin

from .models import Currency


class CurrencyAdmin(admin.ModelAdmin):
    list_display = ("name", "currency_code", "cb_price")


admin.site.register(Currency, CurrencyAdmin)
