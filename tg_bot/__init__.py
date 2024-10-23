from decimal import Decimal
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext
from bot.models import Registration
from conversion.models import Conversion
from currency.models import Currency
from constants import *
from user.models import User
from utils import distribute
import re

# Start REPLY
hi_reply = str("<b>Assalomu alaykum 😊\n\nMarhamat ismingizni kiriting 👇</b>")

# PHONE REPLY
phone_reply = str("<b>Telefon raqamingizni jo'nating 📱</b>")
wrongFormatException = str(
    "<b>Noto'g'ri formatdagi telefon raqam jo'natdingiz❗️\nU quyidagicha ko'rinishda bo'lishi kerak👇\n\n+998 xxx xxx xxx\n 998 xxx xxx xxx</b>")

# CURRENCY REPLY
curency_reply = str("<b>Qaysi valyutada ayriboshlaysiz❓</b>")

# ALL CURRENCIES
currencies = Currency.objects.all().values_list('name', flat=True)
currency_buttons = distribute(list(currencies), chunk_size=2)


class Bot:
    def add_handlers(self):
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start)],
            states={
                ASK_NAME: [MessageHandler(filters.TEXT, self.ask_name)],
                ASK_PHONE: [MessageHandler(filters.ALL | filters.CONTACT, self.ask_phone)],
                ASK_CURRENCY: [MessageHandler(filters.TEXT, self.ask_currency)],
                SELECT_ACTION: [MessageHandler(filters.TEXT, self.select_action)],
                ENTER_AMOUNT: [MessageHandler(filters.TEXT, self.enter_amount)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )
        self.application.add_handler(conv_handler)

    def __init__(self, token):
        self.application = ApplicationBuilder().token(token).build()
        self.add_handlers()

    async def start(self, update: Update, context: CallbackContext) -> int:
        chat_id = update.message.from_user.id
        try:
            user = User.objects.get(chat_id=chat_id)
            await update.message.reply_text(f"Xush kelibsiz {user.name} 😊", reply_markup=ReplyKeyboardRemove(), parse_mode='HTML')
            await update.message.reply_text(curency_reply, reply_markup=ReplyKeyboardMarkup(currency_buttons + [[BACK]], one_time_keyboard=True, resize_keyboard=True), parse_mode='HTML')
            context.user_data['name'] = user.name
            context.user_data['phone'] = user.phone_number
            return ASK_CURRENCY
        except User.DoesNotExist:
            await update.message.reply_text("<b>Assalomu alaykum 😊\n\nMarhamat ismingizni kiriting 👇</b>", reply_markup=ReplyKeyboardRemove(), parse_mode='HTML')
            return ASK_NAME

    async def ask_name(self, update: Update, context: CallbackContext) -> int:
        context.user_data['name'] = update.message.text
        button = KeyboardButton(
            text="Telefon raqamni ulashish 📞", request_contact=True)
        keyboard = ReplyKeyboardMarkup(
            [[button], [BACK]], one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text("<b>Telefon raqamingizni jo'nating 📱</b>", reply_markup=keyboard, parse_mode='HTML')
        return ASK_PHONE

    async def ask_phone(self, update: Update, context: CallbackContext) -> int:
        message = update.message
        phone_rep_btn = KeyboardButton(
            text="Telefon raqamni ulashish 📞", request_contact=True)
        to_ask_phone = ReplyKeyboardMarkup([[phone_rep_btn], [KeyboardButton(
            BACK)]], one_time_keyboard=True, resize_keyboard=True)
        to_currency = ReplyKeyboardMarkup(
            currency_buttons + [[BACK]], one_time_keyboard=True, resize_keyboard=True)

        if message.text == BACK:
            await update.message.reply_text(f"{hi_reply}", reply_markup=ReplyKeyboardRemove(), parse_mode='HTML')
            return ASK_NAME

        if message.contact:
            contact = message.contact
            phone_number = contact.phone_number
            context.user_data['phone'] = phone_number
            await self.register_user(update, context)
            await update.message.reply_text(curency_reply, reply_markup=to_currency, parse_mode='HTML')
            return ASK_CURRENCY

        if message.text:
            phone_number = message.text
            is_match = re.match(UZBEK_PHONE_REGEX, phone_number)

            if is_match is None:
                await update.message.reply_text(wrongFormatException, reply_markup=to_ask_phone, parse_mode='HTML')
                return ASK_PHONE

            context.user_data['phone'] = phone_number
            await self.register_user(update, context)
            await update.message.reply_text(curency_reply, reply_markup=to_currency, parse_mode='HTML')
            return ASK_CURRENCY

        await update.message.reply_text("<b>Iltimos, telefon raqamingizni ulashing yoki kiriting</b>", reply_markup=to_ask_phone, parse_mode='HTML')
        return ASK_PHONE

    async def register_user(self, update: Update, context: CallbackContext) -> None:
        """ Register the user with chat_id, phone number, and name. """
        chat_id = update.message.from_user.id
        name = context.user_data['name']
        phone = context.user_data['phone']

        if User.objects.filter(phone_number=phone).exists():
            await update.message.reply_text("Bu telefon raqami allaqachon ro'yxatdan o'tgan.")
            return

        if not User.objects.filter(chat_id=chat_id).exists():
            User.objects.create(chat_id=chat_id, name=name, phone_number=phone)
            await update.message.reply_text("Foydalanuvchi muvaffaqiyatli ro'yxatdan o'tkazildi.")
        else:
            await update.message.reply_text("Siz allaqachon ro'yxatdan o'tgansiz.")

    async def ask_currency(self, update: Update, context: CallbackContext) -> int:
        selected_currency = update.message.text

        valid_currency = Currency.objects.filter(
            name=selected_currency).first()

        to_currency = ReplyKeyboardMarkup(
            currency_buttons + [[BACK]], one_time_keyboard=True, resize_keyboard=True)

        phone_rep_btn = KeyboardButton(
            text="Telefon raqamni ulashish 📞", request_contact=True)
        to_ask_phone = ReplyKeyboardMarkup([[phone_rep_btn], [KeyboardButton(
            BACK)]], one_time_keyboard=True, resize_keyboard=True)

        if selected_currency == BACK and User.DoesNotExist:
            if not User.DoesNotExist:
                await update.message.reply_text(f"<b>Hurmatli mijoz. Siz ro'yxatdan o'tib bo'lgansiz😊\n\nO'zingizga kerak bo'lgan valyutani tanlang👇</b>", parse_mode='HTML')
                return ASK_CURRENCY
            await update.message.reply_text(f"{phone_reply}", reply_markup=to_ask_phone, parse_mode='HTML')
            return ASK_PHONE

        if valid_currency is None or selected_currency != valid_currency.name:
            await update.message.reply_text(
                "<b>Noto'g'ri valyuta tanladingiz. Qayta tanlang:</b>",
                reply_markup=to_currency,
                parse_mode='HTML'
            )
            return ASK_CURRENCY

        context.user_data['currency'] = valid_currency

        buttons = [BUY, SELL]
        keyboard = ReplyKeyboardMarkup(
            [buttons, [BACK]], one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(f"<b>{selected_currency}ni sotish yoki sotib olish</b>", reply_markup=keyboard, parse_mode='HTML')

        return SELECT_ACTION

    async def select_action(self, update: Update, context: CallbackContext) -> int:
        action = update.message.text
        currency = context.user_data['currency']

        if action == BUY:
            await update.message.reply_text(f"Siz {currency.name} sotib olmoqchisiz. Miqdorni kiriting: ")
        elif action == SELL:
            await update.message.reply_text(f"Siz {currency.name} sotmoqchisiz. Miqdorni kiriting:")

        context.user_data['action'] = action
        return ENTER_AMOUNT

    async def enter_amount(self, update: Update, context: CallbackContext) -> int:
        amount = Decimal(update.message.text)
        action = context.user_data['action']
        currency = context.user_data['currency']

        # if action == BACK:


        if action == BUY:
            converted_amount = Decimal(amount * currency.cb_price)
            await update.message.reply_text(
                f"Siz {amount} {currency.name} sotib oldingiz. Bu {
                    converted_amount} UZS ga teng."
            )
        elif action == SELL:
            converted_amount = Decimal(amount * currency.cb_price)
            await update.message.reply_text(
                f"Siz {amount} {currency.name} sotdingiz. Bu {
                    converted_amount} UZS ga teng."
            )

        try:
            user = User.objects.get(chat_id=update.message.from_user.id)
        except User.DoesNotExist:
            await update.message.reply_text("Foydalanuvchi topilmadi. Iltimos, qaytadan boshlang.")
            return ConversationHandler.END

        if not currency or not hasattr(currency, 'name'):
            await update.message.reply_text("Valyuta topilmadi. Iltimos, qaytadan boshlang.")
            return ASK_CURRENCY

        try:
            Conversion.objects.create(
                user=user,
                currency=currency,
                amount=amount,
                convert_sum=converted_amount
            )
            await update.message.reply_text("Amaliyot muvaffaqiyatli saqlandi.")
        except Exception as e:
            await update.message.reply_text(f"Xatolik yuz berdi: {str(e)}")
            return ConversationHandler.END

        return ConversationHandler.END

    async def cancel(self, update: Update, context: CallbackContext):
        await update.message.reply_text('Operatsiya bekor qilindi.')
        return ConversationHandler.END

    def run(self):
        self.application.run_polling()
