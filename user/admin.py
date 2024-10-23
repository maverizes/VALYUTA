from django.contrib import admin

from user.models import User


class UserAdmin(admin.ModelAdmin):
    list_display = ("name","phone_number", "registered_at")


admin.site.register(User, UserAdmin)
