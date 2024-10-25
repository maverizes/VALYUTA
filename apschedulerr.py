from constants import *
from currency.models import Currency
from user.models import User
from telegram.ext import CallbackContext,ContextTypes


async def send_daily_currency_rates(context: ContextTypes.DEFAULT_TYPE):
    """Send currency rates for USD, RUB, EUR at 8:00 AM to all users."""
    
    # Fetch the current currency rates from the database
    usd_currency = Currency.objects.get(name=USD)
    rub_currency = Currency.objects.get(name=RUB)
    eur_currency = Currency.objects.get(name=EUR)

    # Format the rates and the message
    message = (
        f"🔁Valyutalar kursi yangilandi:\n"
        f"\n📤{USD}ni sotish: {round(usd_currency.cb_price, 2)} {UZS}, 📥{USD}ni sotib olish: {round(usd_currency.cb_price, 2)} {UZS}\n"
        f"\n📤{RUB}ni sotish: {round(rub_currency.cb_price, 2)} {UZS}, 📥{RUB}ni sotib olish: {round(rub_currency.cb_price, 2)} {UZS}\n"
        f"\n📤{EUR}ni sotish: {round(eur_currency.cb_price, 2)} {UZS}, 📥{EUR}ni sotib olish: {round(eur_currency.cb_price, 2)} {UZS}\n"
    )

    users = User.objects.all()

    for user in users:
        chat_id = user.chat_id
        try:
            await context.bot.copy_message(chat_id=chat_id, text=message, parse_mode='HTML')
        except Exception as e:
            print(f"Failed to send message to {chat_id}: {str(e)}")