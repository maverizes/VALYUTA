from django.shortcuts import render
from rest_framework.generics import ListCreateAPIView
from currency.models import Currency
from currency.serializers import CurrencySerializer


class CurrencyList(ListCreateAPIView):
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer
