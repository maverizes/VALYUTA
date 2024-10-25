from django.contrib import admin

from .models import Conversion


class ConversionAdmin(admin.ModelAdmin):
    list_display = ("user", "currency",
                    "direction",
                    "amount", "convert_sum", "convert_date")


admin.site.register(Conversion, ConversionAdmin)
