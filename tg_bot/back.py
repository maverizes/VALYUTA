# back.py
from telegram import ReplyKeyboardRemove, Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import CallbackContext
from constants import *


class Back:
    async def back_to_start(update: Update, context: CallbackContext) -> int:
        await update.message.reply_text(
            "<b>Assalomu alaykum 😊\n\nMarhamat ismingizni kiriting 👇</b>",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode='HTML'
        )
        print("Back to Start Called")
        return ASK_NAME

    async def back_to_ask_phone(update: Update, context: CallbackContext) -> int:
        phone_rep_btn = KeyboardButton(text="Telefon raqamni ulashish 📞", request_contact=True)
        to_ask_phone = ReplyKeyboardMarkup([[phone_rep_btn], [BACK]], one_time_keyboard=True, resize_keyboard=True)

        await update.message.reply_text(
            "<b>Telefon raqamingizni jo'nating 📱</b>",
            reply_markup=to_ask_phone,
            parse_mode='HTML'
        )
        print("Back to Ask Phone Called")
        return ASK_PHONE  # Ensure it returns ASK_PHONE
