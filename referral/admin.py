from django.contrib import admin

from referral.models import Referral

# Register your models here.


class RefAdmin(admin.ModelAdmin):
    list_display = ("name","code")


admin.site.register(Referral, RefAdmin)