
import requests
from django.core.management.base import BaseCommand

from currency.models import Currency

class Command(BaseCommand):
    help = 'Synchronize currency data with NBU API every 5 minutes.'

    def handle(self, *args, **kwargs):
        url = "https://www.nbu.uz/en/exchange-rates/json/"
        try:
            response = requests.get(url)
            response.raise_for_status()
            currencies = response.json()
            for currency_data in currencies:
                name = currency_data.get('title')
                currency_code = currency_data.get('code')
                cb_price = currency_data.get('cb_price')

                if cb_price is not None:
                    cb_price = float(cb_price.replace(",", ""))
                Currency.objects.update_or_create(
                    currency_code=currency_code,
                    defaults={'name': name, 'cb_price': cb_price}
                )

            self.stdout.write(self.style.SUCCESS('Currency data synchronized successfully.'))
        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f"Failed to fetch currency data: {e}"))
