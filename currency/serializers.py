from rest_framework import serializers

from currency.models import Currency


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name', 'currency_code', 'cb_price')
        model = Currency
