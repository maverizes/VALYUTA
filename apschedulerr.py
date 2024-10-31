from constants import *
from currency.models import Currency
from user.models import User
from telegram.ext import ContextTypes

import requests
from currency.models import Currency

import pytz
from datetime import time
from telegram.ext import ContextTypes
from currency.models import Currency
from user.models import User

async def send_daily_currency_rates(context: ContextTypes.DEFAULT_TYPE):
    usd_currency = Currency.objects.get(name=USD)
    rub_currency = Currency.objects.get(name=RUB)
    eur_currency = Currency.objects.get(name=EUR)

    message = (
        f"🔁Valyutalar kursi yangilandi:\n"
        f"\n💵Dollar narxi: {round(usd_currency.cb_price, 2)} so'm\n"
        f"\n🇷🇺Rubl narxi: {round(rub_currency.cb_price, 2)} so'm\n"
        f"\n💶Yevro narxi: {round(eur_currency.cb_price, 2)} so'm\n"
    )

    users = User.objects.all()

    for user in users:
        chat_id = user.chat_id
        try:
            await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')
        except Exception as e:
            print(f"Failed to send message to {chat_id}: {str(e)}")



CURRS = {
    "USD": USD,
    "RUB": RUB,
    "EUR": EUR
}


def sync_currencies():
    url = "https://nbu.uz/uz/exchange-rates/json/"

    try:
        response = requests.get(url)
        response.raise_for_status()  
        currency_data = response.json()

        for item in currency_data:
            code = item.get("code")
            cb_price = item.get("nbu_cell_price")
            name = item.get("title")

            if not cb_price or not code:
                continue

            currency, created = Currency.objects.update_or_create(
                currency_code=code,
                defaults={
                    "name": CURRS.get(code, name),
                    "cb_price": cb_price,
                }
            )
            if created:
                print(f"Created new currency: {currency}")
            else:
                print(f"Updated currency: {currency}")


    except requests.RequestException as e:
        print(f"Error fetching currency data: {e}")
