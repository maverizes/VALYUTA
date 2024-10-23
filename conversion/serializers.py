from rest_framework import serializers

from .models import Conversion


class ConversionSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("id", "user", "currency",
                  "amount", "convert_sum", "convert_date")
        model = Conversion
