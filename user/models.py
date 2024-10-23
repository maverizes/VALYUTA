from django.db import models


class User(models.Model):
    chat_id = models.CharField(max_length=64, primary_key=True)  
    name = models.CharField(max_length=64)
    phone_number = models.CharField(max_length=64)  
    registered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"User: {self.name}"
