from django.urls import path

from currency.views import CurrencyList


urlpatterns = [
    path("", CurrencyList.as_view())
]
