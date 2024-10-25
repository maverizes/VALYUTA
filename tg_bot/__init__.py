<<<<<<< HEAD
from telegram.ext.filters import MessageFilter
from decimal import Decimal, InvalidOperation
from io import BytesIO
=======
>>>>>>> f107077e8e955be8bef62d2acb618402547cbd0e
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext
from apschedulerr import send_daily_currency_rates
from bot.models import Registration
from conversion.models import Conversion
from currency.models import Currency
from constants import *
from tg_bot.exclude import EXCLUDE
from user.models import User
import asyncio
from datetime import datetime, time
import pandas as pd
from django.db.models import Count
from utils import distribute
from decimal import Decimal, InvalidOperation
import re

from telegram.ext import PicklePersistence


from icecream import ic


# Start REPLY
hi_reply = str("<b>Assalomu alaykum 😊\n\nIltimos ismingizni kiriting 👇</b>")
phone_reply = str(
    "<b>Hurmatli mijoz telefon raqamingizni jo'nating yoki pastdagi tugmani bosing📱</b>")
wrong_format_exception = str(
    "<b>Noto'g'ri formatdagi telefon raqam jo'natdingiz❗️\nTelefon raqam quyidagicha ko'rinishda bo'lishi kerak👇\n\n+998 xxx xxx xxx\n 998 xxx xxx xxx</b>")

# Main menu buttons
main_buttons = [
    [f"{USD}"],
    [f"{RUB}", f"{EUR}"],
    [f"{SHOW_OTHER_CURRENCIES}"]
]


class Bot:
    def add_handlers(self):
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start), CommandHandler(
                'admin', self.admin_start)],
            states={
                ASK_NAME: [MessageHandler(filters.TEXT & EXCLUDE, self.ask_name),
                           MessageHandler(filters.ALL, self.ask_name_wrong)],
                ASK_PHONE: [MessageHandler(filters.TEXT | filters.CONTACT, self.ask_phone)],
                SELECT_ACTION: [MessageHandler(filters.TEXT & EXCLUDE, self.select_action)],
                ENTER_AMOUNT: [MessageHandler(filters.TEXT & EXCLUDE, self.enter_amount)],
                SHOW_OTHER_CURRENCIES: [MessageHandler(filters.TEXT & EXCLUDE, self.show_other_currencies)],
                ASK_ADMIN_LOGIN: [MessageHandler(filters.TEXT & EXCLUDE, self.ask_admin_login)],
                ASK_ADMIN_PASSWORD: [MessageHandler(filters.TEXT & EXCLUDE, self.ask_admin_password)],
                ADMIN_MENU_STATE: [MessageHandler(filters.TEXT & EXCLUDE, self.admin_menu)],
                START: [MessageHandler(filters.TEXT & EXCLUDE, self.show_main_menu)],
                POST_MESSAGE: [MessageHandler(
                    filters.TEXT & EXCLUDE, self.handle_post)]
            },
            fallbacks=[
                CommandHandler('start', self.start),
                CommandHandler('admin', self.admin_start)
            ],
            persistent=True,
            name="MainConversation"
        )

        self.application.add_handler(conv_handler)

    def __init__(self, token):

        persistence = PicklePersistence(
            "persistence.pickle", update_interval=1)

        self.application = ApplicationBuilder().token(
            token).persistence(persistence).build()
        self.add_handlers()

        daily_time = time(hour=8, minute=0)
        self.application.job_queue.run_daily(
            send_daily_currency_rates, time=daily_time
        )

    async def store_message_id(self, update: Update, context: CallbackContext):
        if 'message_ids' not in context.user_data:
            context.user_data['message_ids'] = []
        context.user_data['message_ids'].append(update.message.message_id)

    async def send_message(self, update: Update, context: CallbackContext, text: str, reply_markup=None):
        message = await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
        if 'message_ids' not in context.user_data:
            context.user_data['message_ids'] = []
        context.user_data['message_ids'].append(message.message_id)

    async def start(self, update: Update, context: CallbackContext) -> int:
        context.user_data.clear()
        context.user_data['chat_id'] = update.message.from_user.id

        referrer_chat_id = None
        if context.args:
            referrer_chat_id = context.args[0]

        await self.store_message_id(update, context)

        try:
            user = User.objects.get(chat_id=context.user_data['chat_id'])
            await self.show_main_menu(update, context)
            return SELECT_ACTION
        except User.DoesNotExist:
            if referrer_chat_id:
                try:
                    referrer = User.objects.get(chat_id=referrer_chat_id)
                    # Save referrer for registration
                    context.user_data['referrer'] = referrer
                except User.DoesNotExist:
                    context.user_data['referrer'] = None  # Referrer not found

            await self.send_message(update, context, hi_reply, reply_markup=ReplyKeyboardRemove())
            return ASK_NAME

    async def show_main_menu(self, update: Update, context: CallbackContext) -> int:
        usd_currency = Currency.objects.filter(name=USD).first()
        rub_currency = Currency.objects.filter(name=RUB).first()
        eur_currency = Currency.objects.filter(name=EUR).first()

        usd_price = usd_currency.cb_price if usd_currency else "N/A"
        rub_price = rub_currency.cb_price if rub_currency else "N/A"
        eur_price = eur_currency.cb_price if eur_currency else "N/A"

        currency_rates_message = (
            f"{USD}ning bugungi narxi: {usd_price} {SUM}\n"
            f"\n{RUB}ning bugungi narxi: {rub_price} {SUM}\n"
            f"\n{EUR}ning bugungi narxi: {eur_price} {SUM}"
        )

        keyboard = ReplyKeyboardMarkup(
            main_buttons, one_time_keyboard=True, resize_keyboard=True
        )

        user = User.objects.get(chat_id=update.message.from_user.id)

        message_text = (
            f"<b>Assalomu alaykum {user.name} !\n"
            f"Sizni Dollarchi botimizda ko'rib turganimizdan xursandmiz😊\n\n"
            f"{currency_rates_message}\n\n"
            f"Kerakli amaliyotni tanlang👇</b>\n\n"
        )

        await self.send_message(
            update, context, message_text, reply_markup=keyboard
        )
        return SELECT_ACTION

    async def check_command(self, update: Update, context: CallbackContext) -> bool:
        command = update.message.text
        if command == "/start":
            await self.start(update, context)
            return True
        elif command == "/admin":
            await self.admin_start(update, context)
            return True
        return False

    async def ask_name_wrong(self, update: Update, context: CallbackContext):
        await update.message.reply_text("Iltimos ismingizni to'g'ri kiriting!")

    async def ask_name(self, update: Update, context: CallbackContext) -> int:

        context.user_data['name'] = update.message.text
        button = KeyboardButton(
            text="Telefon raqamni ulashish 📞", request_contact=True)
        keyboard = ReplyKeyboardMarkup(
            [[button], [BACK]], one_time_keyboard=True, resize_keyboard=True)

        await self.send_message(update, context, phone_reply, reply_markup=keyboard)
        return ASK_PHONE

    async def ask_phone(self, update: Update, context: CallbackContext) -> int:
        message = update.message.text

        if message == '/start':
            return await self.start(update, context)
        elif message == '/admin':
            return await self.admin_start(update, context)

        await self.store_message_id(update, context)

        phone_rep_btn = KeyboardButton(
            text="Telefon raqamni ulashish 📞", request_contact=True)
        to_ask_phone = ReplyKeyboardMarkup([[phone_rep_btn], [KeyboardButton(BACK)]], one_time_keyboard=True,
                                           resize_keyboard=True)

        if message == BACK:
            await self.send_message(update, context, hi_reply, reply_markup=ReplyKeyboardRemove())
            return ASK_NAME

        if update.message.contact:
            phone_number = self.format_phone_number(
                update.message.contact.phone_number)
            context.user_data['phone'] = phone_number
            await self.register_user(update, context)
            return SELECT_ACTION

        if update.message.text:
            phone_number = self.format_phone_number(update.message.text)
            is_match = re.match(UZBEK_PHONE_REGEX, phone_number)

            if is_match is None:
                await self.send_message(update, context, wrong_format_exception, reply_markup=to_ask_phone)
                return ASK_PHONE

            context.user_data['phone'] = phone_number
            await self.register_user(update, context)
            return SELECT_ACTION

        await self.send_message(update, context, f"<b>Hurmatli mijoz telefon raqamingizni jo'nating \nyoki \"Telefoni raqamni ulashish\" tugamasini bosing 👇</b>", reply_markup=to_ask_phone)
        return ASK_PHONE

    def format_phone_number(self, phone_number: str) -> str:
        phone_number = re.sub(r'\D', '', phone_number)
        if not phone_number.startswith('998'):
            phone_number = '998' + phone_number
        return f'+{phone_number}'

    async def register_user(self, update: Update, context: CallbackContext) -> None:
        chat_id = update.message.from_user.id
        username = update.message.from_user.username
        name = context.user_data['name']
        phone = context.user_data['phone']

        referrer = context.user_data.get('referrer')

        if not User.objects.filter(chat_id=chat_id).exists():
            new_user = User.objects.create(
                chat_id=chat_id, name=name, username=username, phone_number=phone, referrer=referrer)

            if referrer:
                referrer.referral_count += 1
                referrer.save()

            await asyncio.sleep(2)
            await self.show_main_menu(update, context)
        else:
<<<<<<< HEAD
            await self.send_message(update, context, "Siz allaqachon ro'yxatdan o'tgansiz✅")
            await self.show_main_menu(update, context)
=======
            await update.message.reply_text("Siz allaqachon ro'yxatdan o'tgansiz.")

    async def ask_currency(self, update: Update, context: CallbackContext) -> int:
        selected_currency = update.message.text

        valid_currency = Currency.objects.filter(name=selected_currency).first()

        to_currency = ReplyKeyboardMarkup(
            currency_buttons + [[BACK]], one_time_keyboard=True, resize_keyboard=True)

        phone_rep_btn = KeyboardButton(
            text="Telefon raqamni ulashish 📞", request_contact=True)
        to_ask_phone = ReplyKeyboardMarkup([[phone_rep_btn], [KeyboardButton(
            BACK)]], one_time_keyboard=True, resize_keyboard=True)

        if selected_currency == BACK:
            await update.message.reply_text(f"{phone_reply}", reply_markup=to_ask_phone, parse_mode='HTML')
            return ASK_PHONE

        if valid_currency is None or selected_currency != valid_currency.name:
            await update.message.reply_text(
                "<b>Noto'g'ri valyuta tanladingiz. Qayta tanlang 👇:</b>",
                reply_markup=to_currency,
                parse_mode='HTML'
            )
            return ASK_CURRENCY

        context.user_data['currency'] = valid_currency

        # Offer two options: currency to UZS or UZS to currency
        buttons = [[f"{valid_currency.currency_code} → {UZS}"], [f"{UZS} → {valid_currency.currency_code}"], [BACK]]
        keyboard = ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True)

        await update.message.reply_text(f"<b>{selected_currency} tanlandi\nKerakli amaliyotni tanlang👇</b>", reply_markup=keyboard, parse_mode='HTML')

        return SELECT_ACTION
>>>>>>> f107077e8e955be8bef62d2acb618402547cbd0e


    async def select_action(self, update: Update, context: CallbackContext) -> int:
        await self.store_message_id(update, context)
        action = update.message.text

<<<<<<< HEAD
        if action == '/start':
            return await self.start(update, context)

        if action == SHOW_OTHER_CURRENCIES:
            await self.show_other_currencies(update, context)
            return SHOW_OTHER_CURRENCIES

        if action == BACK:
            await self.show_main_menu(update, context)
            return SELECT_ACTION

        chosen_currency = Currency.objects.filter(name=action).first()

        if chosen_currency:
            context.user_data['currency'] = chosen_currency
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            currency_info_message = (
                f"<b>🌍{current_time} vaqtiga ko'ra hozir\n\n"
                f"{chosen_currency.name} ning narxi: {
                    chosen_currency.cb_price} {UZS}\n </b>"
            )
            await self.send_message(update, context, currency_info_message)

            conversion_buttons = [
                [f"{chosen_currency.name} → {UZS}"],
                [f"{UZS} → {chosen_currency.name}"],
                [BACK]
            ]
            keyboard = ReplyKeyboardMarkup(
                conversion_buttons, one_time_keyboard=True, resize_keyboard=True)

            await self.send_message(update, context, "<b>Pastdagi tugmalardan kerakli amaliyotni tanlang👇 </b>", reply_markup=keyboard)
            return SELECT_ACTION

        elif "→" in action:
            if f"{UZS}" in action.split("→")[1].strip():
                context.user_data['conversion_direction'] = "to_uzs"
            else:
                context.user_data['conversion_direction'] = "from_uzs"

            chosen_currency = context.user_data.get('currency')
            conversion_direction = context.user_data.get(
                'conversion_direction')

            if conversion_direction == "to_uzs":
                await self.send_message(update, context, f"<b>{chosen_currency.name} miqdorini kiriting👇</b>",
                                        reply_markup=ReplyKeyboardMarkup([[BACK]], resize_keyboard=True, one_time_keyboard=True))
            elif conversion_direction == "from_uzs":
                await self.send_message(update, context, f"<b>{UZS} miqdorini kiriting👇</b>",
                                        reply_markup=ReplyKeyboardMarkup([[BACK]], resize_keyboard=True, one_time_keyboard=True))

            return ENTER_AMOUNT

        else:
            await self.send_message(update, context, "<b>Kerakli valyutani tanlang❗️</b>", reply_markup=ReplyKeyboardMarkup([[BACK]], one_time_keyboard=True, resize_keyboard=True))
            return SELECT_ACTION

    async def show_other_currencies(self, update: Update, context: CallbackContext) -> int:
        await self.store_message_id(update, context)

        if update.message.text == BACK:
            await self.show_main_menu(update, context)
            return SHOW_OTHER_CURRENCIES

        other_currencies = Currency.objects.exclude(
            name__in=[USD, RUB, EUR]).values_list('name', flat=True)
        currency_buttons = distribute(list(other_currencies), chunk_size=2)

        chosen_currency = Currency.objects.filter(
            name=update.message.text).first()

        if chosen_currency:
            context.user_data['currency'] = chosen_currency
            conversion_buttons = [
                [f"{chosen_currency.name} → {UZS}"],
                [f"{UZS} → {chosen_currency.name}"],
                [BACK]
            ]
            keyboard = ReplyKeyboardMarkup(
                conversion_buttons, one_time_keyboard=True, resize_keyboard=True)
            await self.send_message(update, context, f"<b>{chosen_currency.name} valyutasini tanladingiz. Kerakli amaliyotni tanlang:</b>", reply_markup=keyboard)
            return SELECT_ACTION
        else:
            keyboard = ReplyKeyboardMarkup(
                [[BACK]] + currency_buttons, one_time_keyboard=True, resize_keyboard=True)
            await self.send_message(update, context, "<b>Boshqa valyutalarni tanlang:</b>", reply_markup=keyboard)
            return SELECT_ACTION
=======
        # Determine the direction of conversion
        if f"{currency.currency_code} → {UZS}" in action:
            context.user_data['conversion_direction'] = "to_uzs"
            await update.message.reply_text(f"Siz {currency.currency_code} ni UZSga almashtirmoqchisiz. {currency.currency_code} miqdorni kiriting: ")
        elif f"{UZS} → {currency.currency_code}" in action:
            context.user_data['conversion_direction'] = "from_uzs"
            await update.message.reply_text(f"Siz {UZS} ni {currency.currency_code} ga almashtirmoqchisiz. UZS miqdorini:")

        return ENTER_AMOUNT
>>>>>>> f107077e8e955be8bef62d2acb618402547cbd0e


    async def enter_amount(self, update: Update, context: CallbackContext) -> int:
<<<<<<< HEAD
        if update.message.text == '/start':
            return await self.start(update, context)

        if update.message.text == BACK:
            chosen_currency = context.user_data['currency']
            conversion_buttons = [
                [f"{chosen_currency.name} → {UZS}"],
                [f"{UZS} → {chosen_currency.name}"],
                [BACK]
            ]
            keyboard = ReplyKeyboardMarkup(
                conversion_buttons, one_time_keyboard=True, resize_keyboard=True)
            await self.send_message(update, context, f"<b>{chosen_currency.name} valyutasini tanladingiz. Kerakli amaliyotni tanlang:</b>", reply_markup=keyboard)
            return SELECT_ACTION

        await self.store_message_id(update, context)

        try:
            amount = Decimal(update.message.text)
        except InvalidOperation:
            await self.send_message(update, context, "Iltimos, to'g'ri miqdorni kiriting.", ReplyKeyboardMarkup([[BACK]], resize_keyboard=True, one_time_keyboard=True))
            return ENTER_AMOUNT

=======
        try:
            amount = Decimal(update.message.text)
        except InvalidOperation:
            await update.message.reply_text("Iltimos, to'g'ri miqdorni kiriting.")
            return ENTER_AMOUNT
        
        direction = context.user_data['conversion_direction']
>>>>>>> f107077e8e955be8bef62d2acb618402547cbd0e
        currency = context.user_data['currency']
        conversion_direction = context.user_data.get('conversion_direction')

<<<<<<< HEAD
        if conversion_direction not in ["to_uzs", "from_uzs"]:
            await self.send_message(update, context, "Xato: yo'nalish noto'g'ri belgilangan.")
            return ENTER_AMOUNT

        model_direction = "TO_UZS" if conversion_direction == "to_uzs" else "FROM_UZS"
        if conversion_direction == "to_uzs":
            ic(amount, currency.cb_price, amount * currency.cb_price)
            converted_amount = round(amount * currency.cb_price, 2)
            await self.send_message(update, context, f"Siz {amount} {currency.name} ni {converted_amount} {UZS} ga almashtirdingiz.", reply_markup=ReplyKeyboardMarkup([[BACK]], resize_keyboard=True, one_time_keyboard=True))
        else:
            converted_amount = round(amount / currency.cb_price, 2)
            await self.send_message(update, context, f"Siz {amount} {UZS} ni {converted_amount} {currency.name} ga almashtirdingiz.", reply_markup=ReplyKeyboardMarkup([[BACK]], resize_keyboard=True, one_time_keyboard=True))

        user = User.objects.get(chat_id=update.message.from_user.id)

        Conversion.objects.create(
            user=user, currency=currency, amount=amount, direction=model_direction, convert_sum=converted_amount)

    async def admin_start(self, update: Update, context: CallbackContext) -> int:
        await update.message.reply_text("<b>Admin parolingizni kiriting: </b>", reply_markup=ReplyKeyboardRemove(), parse_mode='HTML')
        return ASK_ADMIN_LOGIN

    async def ask_admin_login(self, update: Update, context: CallbackContext) -> int:
        login = update.message.text
        context.user_data['admin_login'] = login
        await update.message.reply_text("<b>Parolingizni kriting: </b>", parse_mode='HTML')
        return ASK_ADMIN_PASSWORD

    async def ask_admin_password(self, update: Update, context: CallbackContext) -> int:
        password = update.message.text
        login = context.user_data.get('admin_login')

        if login == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            await update.message.reply_text(
                "<b>✅ Parol tasdiqlandi!\n\n👤 ADMIN PANEL </b>",
                reply_markup=ReplyKeyboardMarkup(
                    [[BOT_STATS], [USER_STATS], [START], [POST_MESSAGE]], resize_keyboard=True),
                parse_mode='HTML'
=======
        if direction == "to_uzs":
            converted_amount = Decimal(amount * currency.cb_price)  # Convert currency to UZS
            await update.message.reply_text(
                f"Siz {amount} {currency.currency_code} ni {converted_amount} {UZS} ga almashtirdingiz."
            )
        elif direction == "from_uzs":
            converted_amount = Decimal(amount / currency.cb_price)  # Convert UZS to currency
            await update.message.reply_text(
                f"Siz {amount} {UZS} ni {converted_amount} {currency.currency_code} ga almashtirdingiz."
>>>>>>> f107077e8e955be8bef62d2acb618402547cbd0e
            )
            return ADMIN_MENU_STATE
        await update.message.reply_text("<b>❌ Login yoki parol noto'g'ri. Qayta urinib ko'ring</b>", parse_mode='HTML')

<<<<<<< HEAD
        wrong_password_message = await update.message.reply_text("<b>Asosiy menyuga o'tilmoqda...</b>", parse_mode='HTML')

        return await self.show_main_menu(update, context)

    async def admin_menu(self, update: Update, context: CallbackContext) -> int:
        action = update.message.text
        if action == BOT_STATS:
            await self.generate_bot_statistics(update, context)
            return ADMIN_MENU_STATE
        elif action == USER_STATS:
            await self.generate_user_statistics(update, context)
            return ADMIN_MENU_STATE
        elif action == POST_MESSAGE:
            await update.message.reply_text("📤 Yangi post yuboring:", reply_markup=ReplyKeyboardMarkup([[BACK]], one_time_keyboard=True, resize_keyboard=True))
            return POST_MESSAGE
        else:
            await update.message.reply_text("Noto'g'ri amal kiritdingiz❗️ \n\nIltimos quyidagi tugmalardan birini tanlang👇",
                                            reply_markup=ReplyKeyboardMarkup([[BOT_STATS], [USER_STATS], [POST_MESSAGE], [BACK]], resize_keyboard=True), parse_mode='HTML')
            return ADMIN_MENU_STATE
=======
        # Ensure the user exists
        try:
            user = User.objects.get(chat_id=update.message.from_user.id)
        except User.DoesNotExist:
            await update.message.reply_text("Foydalanuvchi topilmadi. Iltimos, qaytadan boshlang.")
            return ConversationHandler.END

        # Create the conversion record if all is valid
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
>>>>>>> f107077e8e955be8bef62d2acb618402547cbd0e

    async def handle_post(self, update: Update, context: CallbackContext) -> int:
        post_content = update.message.text

        all_users = User.objects.values_list('chat_id', flat=True)

        for chat_id in all_users:
            try:
                await context.bot.send_message(chat_id=chat_id, text=post_content, parse_mode='HTML')
            except Exception as e:
                print(f"Xabarni yuborishda xatolik. Chat id: {
                      chat_id}. Xatolik: {e}")

        await update.message.reply_text("Xabar hamma foydalanuvchilarga  muvaffaqiyatli yuborildi❗️", parse_mode='HTML')
        return ADMIN_MENU_STATE

    async def generate_bot_statistics(self, update: Update, context: CallbackContext):
        total_users = User.objects.count()
        total_conversions = Conversion.objects.count()

        conversion_per_currency = Conversion.objects.values(
            'currency__name').annotate(total=Count('id')).order_by('-total')

        message_content = f"📊 <b>Bot statistikasi</b>:\n\n"
        message_content += f"👤 Jami foydalanuvchilar: {total_users}\n"
        message_content += f"💱 Jami ayriboshlaganlar: {total_conversions}\n\n"
        message_content += "💹 <b>Foydalangan valyutalar:</b>\n"

        for currency in conversion_per_currency:
            message_content += f"\n  • <b>{currency['currency__name']}</b>:  \t<b>{
                currency['total']}</b> ta\n"

        await update.message.reply_text(message_content, parse_mode="HTML")

    async def generate_user_statistics(self, update: Update, context: CallbackContext):
        users = User.objects.all()
        conversions = Conversion.objects.all()

        data = []
        auto_increment_id = 1
        for i, user in enumerate(users, 1):
            user_conversions = conversions.filter(user=user)
            for j, conv in enumerate(user_conversions, 1):
                data.append({
                    "ID": auto_increment_id if j == 1 else "",  # Use the auto-increment ID here
                    "Ism": user.name if j == 1 else "",
                    "username": (f"@{user.username}" if user.username else "N/A") if j == 1 else "",
                    "user_chat_id": user.chat_id if j == 1 else "",
                    "Telefon raqami": user.phone_number if j == 1 else "",
                    "Eng kop foydalangan valyuta": user.favourite_currency,
                    "Ro'yxatdan o'tgan sana": user.registered_at.strftime("%d.%m.%Y"),
                    "Valyutadan": conv.currency.name if conv.direction == "TO_UZS" else "O'zbek so'mi",
                    "Valyutaga": "O'zbek so'mi" if conv.direction == "TO_UZS" else conv.currency.name,
                    "Kurs narxi": conv.currency.cb_price,
                    "Miqdori": conv.amount,
                    "Jami summa": conv.convert_sum,
                    "date_of_conversion": conv.convert_date.strftime("%d.%m.%Y %H:%M:%S"),
                })
                auto_increment_id += 1

        df = pd.DataFrame(data)

        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, index=False, sheet_name='User Statistics')

        writer.close()
        output.seek(0)

        await context.bot.send_document(
            chat_id=update.message.chat_id,
            document=output,
            filename="all_users_statistics.xlsx",
            caption="Here is the user statistics report."
        )

    def run(self):
        self.application.run_polling()
