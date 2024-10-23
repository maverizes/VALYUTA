from django.shortcuts import render
from rest_framework.generics import ListCreateAPIView
from currency.serializers import CurrencySerializer
from bot.currency.models import Currency
# Create your views here.


class CurrencyList(ListCreateAPIView):
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer
