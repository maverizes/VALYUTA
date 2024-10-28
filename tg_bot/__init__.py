import random
import string
from telegram.ext.filters import MessageFilter
from decimal import Decimal, InvalidOperation
from io import BytesIO
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext
from apschedulerr import send_daily_currency_rates, sync_currencies
from bot.models import Registration
from conversion.models import Conversion
from currency.models import Currency
from constants import *
from referral.models import Referral
from tg_bot.exclude import EXCLUDE
from user.models import User
import asyncio
from datetime import datetime, time
import pandas as pd
from django.db.models import Count
from utils import distribute
import re

from telegram.ext import PicklePersistence


from icecream import ic


ic.configureOutput(
    includeContext=True, contextAbsPath=True
)

# Start REPLY
hi_reply = "<b>Assalomu alaykum 😊\n\nIltimos ismingizni kiriting 👇</b>"
phone_reply = "<b>Hurmatli mijoz telefon raqamingizni jo'nating yoki pastdagi tugmani bosing📱</b>"
wrong_format_exception = "<b>Noto'g'ri formatdagi telefon raqam jo'natdingiz❗️\nTelefon raqam quyidagicha ko'rinishda bo'lishi kerak👇\n\n+998 xxx xxx xxx\n 998 xxx xxx xxx</b>"

# Main menu buttons
# main_buttons = [
#     [f"{USD}"],
#     [f"{RUB}", f"{EUR}"],
#     [f"{SHOW_OTHER_CURRENCIES}"]
# ]


post_confirmation_button = [
    ["✅ Postni jo'natish"],
    ["❌ Bekor qilish"]
]


class Bot:
    def add_handlers(self):
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start), CommandHandler(
                'admin', self.admin_start)],
            states={
                ASK_NAME: [MessageHandler(filters.TEXT & EXCLUDE, self.ask_name),
                           MessageHandler(filters.ALL & EXCLUDE, self.ask_name_wrong)],
                ASK_PHONE: [MessageHandler(filters.TEXT | filters.CONTACT, self.ask_phone), self.back(self.start)],
                SELECT_ACTION: [
                    MessageHandler(filters.Text(
                        [SHOW_OTHER_CURRENCIES]), self.show_other_currencies),
                    MessageHandler(filters.TEXT & EXCLUDE, self.select_action),
                    self.back(self.start)],
                ENTER_AMOUNT: [MessageHandler(filters.TEXT & EXCLUDE, self.enter_amount), self.back(self.start)],
                SHOW_OTHER_CURRENCIES: [
                    MessageHandler(filters.TEXT & EXCLUDE,
                                   self.show_other_currencies),
                    # MessageHandler(filters.Text([BACK]),self.start)
                    self.back(self.start)
                ],
                ASK_ADMIN_LOGIN: [MessageHandler(filters.TEXT & EXCLUDE, self.ask_admin_login)],
                ASK_ADMIN_PASSWORD: [MessageHandler(filters.TEXT & EXCLUDE, self.ask_admin_password)],
                ADMIN_MENU_STATE: [MessageHandler(filters.TEXT & EXCLUDE, self.admin_menu)],
                START: [MessageHandler(filters.TEXT & EXCLUDE, self.show_main_menu)],
                POST_MESSAGE: [MessageHandler(filters.ALL, self.handle_post)],
                POST_CONFIRMATION: [MessageHandler(filters.TEXT & EXCLUDE, self.post_confirmation)],
                DELETE_REFERRAL_STATE: [
                    MessageHandler(filters.TEXT & EXCLUDE,
                                   self.delete_referral),
                ],
                REFERRAL_OPTIONS: [
                    MessageHandler(filters.Text(
                        [DELETE_REFERRAL_STATE]), self.delete_referral),
                    # MessageHandler(filters.Text([BACK]), self.referral_menu),
                    self.back(self.referral_menu)
                ],
                REFERRAL_CREATE_NAME: [MessageHandler(filters.TEXT & EXCLUDE, self.create_referral_create_name_uz)],
                CREATE_REFERRAL_STATE: [MessageHandler(filters.TEXT & EXCLUDE, self.referral_menu),
                                        self.back(self.referral_menu)
                                        ],
                REFERRAL_MENU: [
                    MessageHandler(filters.Text([CREATE_REFERRAL_STATE]),
                                   self.create_referral),
                    MessageHandler(filters.TEXT & EXCLUDE,
                                   self.referral_select_referral),

                    # MessageHandler(filters.Text([BACK]), self.start)
                    self.back(self.start)
                ],
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

        # daily_time = time(hour=8, minute=0)
        # self.application.job_queue.run_daily(
        #     send_daily_currency_rates, time=daily_time
        # )

        sync_currencies()

        self.application.job_queue.run_repeating(self.sync_currencies, 300)

    async def store_message_id(self, update: Update, context: CallbackContext):
        if 'message_ids' not in context.user_data:
            context.user_data['message_ids'] = []
        context.user_data['message_ids'].append(update.message.message_id)

    def initialize_bot_data(self):
        if 'referrals' not in self.application.bot_data:
            self.application.bot_data['referrals'] = {}

    async def send_message(self, update: Update, context: CallbackContext, text: str, reply_markup=None):
        message = await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
        if 'message_ids' not in context.user_data:
            context.user_data['message_ids'] = []
        context.user_data['message_ids'].append(message.message_id)

    def back(self, callback) -> MessageHandler:
        return MessageHandler(
            filters.Text(BACK), callback
        )

    async def start(self, update: Update, context: CallbackContext) -> int:
        context.user_data.clear()
        context.user_data['chat_id'] = update.message.from_user.id

        await self.store_message_id(update, context)

        ic("Salommmm")

        user, _ = User.objects.update_or_create(
            chat_id=update.effective_user.id,
            defaults=dict(
                username=update.effective_user.username,
                referral=Referral.objects.filter(
                    code=context.args[0]).first() if context.args else None
            )
        )

        ic(user.name, user.phone_number,
           user.name is None, user.phone_number is None)

        if user.name is None or user.phone_number is None:
            await update.message.reply_text(hi_reply, parse_mode='HTML')
            return ASK_NAME

        if user.is_admin:
            # return await self.admin_menu(update,context)
            await update.message.reply_text(
                "<b>👤 ADMIN PANEL</b>",
                reply_markup=ReplyKeyboardMarkup(
                    [[BOT_STATS, USER_STATS], [POST_MESSAGE], [REFERRAL_MENU], [START], ], resize_keyboard=True),
                parse_mode='HTML'
            )
            return ADMIN_MENU_STATE

        return await self.show_main_menu(update, context)
        # await self.send_message(update, context, hi_reply, reply_markup=ReplyKeyboardRemove())

    async def show_main_menu(self, update: Update, context: CallbackContext):
        usd_currency = Currency.objects.filter(currency_code="USD").first()
        rub_currency = Currency.objects.filter(currency_code="RUB").first()
        eur_currency = Currency.objects.filter(currency_code="EUR").first()

        usd_price = usd_currency.cb_price if usd_currency else "N/A"
        rub_price = rub_currency.cb_price if rub_currency else "N/A"
        eur_price = eur_currency.cb_price if eur_currency else "N/A"

        currency_rates_message = (
            f"{USD}ning bugungi narxi: {usd_price} {SUM}\n"
            f"\n{RUB}ning bugungi narxi: {rub_price} {SUM}\n"
            f"\n{EUR}ning bugungi narxi: {eur_price} {SUM}"
        )

        keyboard = ReplyKeyboardMarkup([
                [
                    usd_currency.name,
                    rub_currency.name
                ],
                [
                    eur_currency.name
                ]
            ], one_time_keyboard=True, resize_keyboard=True
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

    async def ask_name_wrong(self, update: Update, context: CallbackContext):
        await update.message.reply_text("Iltimos ismingizni to'g'ri kiriting!")

    async def ask_name(self, update: Update, context: CallbackContext) -> int:

        # context.user_data['name'] = update.message.text
        user = User.objects.get(chat_id=update.message.from_user.id)

        user.name = update.message.text
        user.save()

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
        user = User.objects.get(chat_id=update.message.from_user.id)

        ic(user)

        if update.message.contact:
            phone_number = self.format_phone_number(
                update.message.contact.phone_number)

            user.phone_number = update.message.contact.phone_number
            user.save()

            ic(user, user.phone_number)

            await self.register_user(update, context)
            return SELECT_ACTION

        if update.message.text:
            phone_number = self.format_phone_number(update.message.text)
            is_match = re.match(UZBEK_PHONE_REGEX, phone_number)

            if is_match is None:
                await self.send_message(update, context, wrong_format_exception, reply_markup=to_ask_phone)
                return ASK_PHONE

            user.phone_number = update.message.text
            user.save()

            ic(user, user.phone_number)

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

        await self.show_main_menu(update, context)

    async def select_action(self, update: Update, context: CallbackContext) -> int:
        await self.store_message_id(update, context)
        action = update.message.text

        # if action == SHOW_OTHER_CURRENCIES:
        #     await self.show_other_currencies(update, context)
        #     return SHOW_OTHER_CURRENCIES

        chosen_currency = Currency.objects.filter(name=action).first()

        ic(chosen_currency, action)

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

        elif chosen_currency == BACK:
            await self.select_action
            return SELECT_ACTION

        else:
            await self.send_message(update, context, "<b>Kerakli valyutani tanlang❗️</b>", reply_markup=ReplyKeyboardMarkup([[BACK]], one_time_keyboard=True, resize_keyboard=True))
            return SELECT_ACTION

    async def show_other_currencies(self, update: Update, context: CallbackContext) -> int:
        await self.store_message_id(update, context)

        # if update.message.text == BACK:
        # await self.show_main_menu(update, context)
        # return SHOW_OTHER_CURRENCIES

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

    async def enter_amount(self, update: Update, context: CallbackContext) -> int:
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

        currency = context.user_data['currency']
        conversion_direction = context.user_data.get('conversion_direction')

        if conversion_direction not in ["to_uzs", "from_uzs"]:
            await self.send_message(update, context, "Xato: yo'nalish noto'g'ri belgilangan.")
            return ENTER_AMOUNT

        model_direction = "TO_UZS" if conversion_direction == "to_uzs" else "FROM_UZS"

        if conversion_direction == "to_uzs":
            converted_amount = round(amount * currency.cb_price, 2)
            await self.send_message(update, context, f"{amount} {currency.name} ➡️ {converted_amount} {SUM} 🇺🇿", reply_markup=ReplyKeyboardMarkup([[BACK]], resize_keyboard=True, one_time_keyboard=True))
        else:
            converted_amount = round(amount / currency.cb_price, 2)
            await self.send_message(update, context, f"{amount} {SUM} 🇺🇿  ➡️ {converted_amount} {currency.name}", reply_markup=ReplyKeyboardMarkup([[BACK]], resize_keyboard=True, one_time_keyboard=True))

        user = User.objects.get(chat_id=update.message.from_user.id)

        Conversion.objects.create(
            user=user, currency=currency, amount=amount, direction=model_direction, convert_sum=converted_amount)

    async def admin_start(self, update: Update, context: CallbackContext) -> int:
        user = User.objects.get(chat_id=update.message.from_user.id)

        if user.is_admin:
            # await update.message.reply_text("Yeb turib marama")
            return await self.start(update, context)

        await update.message.reply_text("<b>Admin loginingizni kiriting: </b>", reply_markup=ReplyKeyboardRemove(), parse_mode='HTML')
        return ASK_ADMIN_LOGIN

    async def ask_admin_login(self, update: Update, context: CallbackContext) -> int:
        login = update.message.text
        context.user_data['admin_login'] = login
        await update.message.reply_text("<b>Parolingizni kiriting: </b>", parse_mode='HTML')
        return ASK_ADMIN_PASSWORD

    async def ask_admin_password(self, update: Update, context: CallbackContext) -> int:
        password = update.message.text
        login = context.user_data.get('admin_login')

        if login == ADMIN_USERNAME and password == ADMIN_PASSWORD:

            user = User.objects.get(chat_id=update.message.from_user.id)
            user.is_admin = True
            user.save()

            return await self.start(update, context)

        await update.message.reply_text("<b>❌ Login yoki parol noto'g'ri. Qayta urinib ko'ring</b>", parse_mode='HTML')

        wrong_password_message = await update.message.reply_text("<b>Asosiy menyuga o'tilmoqda...</b>", parse_mode='HTML')

        return await self.show_main_menu(update, context)

    async def admin_menu(self, update: Update, context: CallbackContext) -> int:
        action = update.message.text
        admin_keyboard = ReplyKeyboardMarkup(
            [[BOT_STATS, USER_STATS],
             [POST_MESSAGE],
             [REFERRAL_MENU],
             [START]],
            resize_keyboard=True,
            one_time_keyboard=True
        )

        if action == BOT_STATS:
            await self.generate_bot_statistics(update, context)
            return ADMIN_MENU_STATE
        elif action == REFERRAL_MENU:
            await self.referral_menu(update, context)
            return REFERRAL_MENU
        elif action == USER_STATS:
            await self.generate_user_statistics(update, context)
            return ADMIN_MENU_STATE
        elif action == START:
            user = User.objects.get(chat_id=update.message.from_user.id)

            user.is_admin = False
            user.save()
            return await self.start(update, context)
            # await self.show_main_menu(update, context)
            # return SELECT_ACTION
        elif action == POST_MESSAGE:
            await update.message.reply_text("📤 Yangi post yuboring:", reply_markup=ReplyKeyboardMarkup([[BACK]], one_time_keyboard=True, resize_keyboard=True))
            return POST_MESSAGE
        else:
            await update.message.reply_text(
                "Iltimos quyidagi tugmalardan birini tanlang👇",
                reply_markup=admin_keyboard,
                parse_mode='HTML'
            )
            return ADMIN_MENU_STATE

    async def handle_post(self, update: Update, context: CallbackContext) -> int:
        message = update.message

        context.user_data['pending_post'] = {
            'chat_id': message.chat_id,
            'message_id': message.message_id
        }

        await context.bot.copy_message(
            chat_id=message.chat_id,
            from_chat_id=message.chat_id,
            message_id=message.message_id
        )

        reply_markup = ReplyKeyboardMarkup(
            [["✅ Postni jo'natish", "❌ Bekor qilish"]],
            one_time_keyboard=True,
            resize_keyboard=True
        )
        await message.reply_text("Postni jo'natishni tasdiqlang yoki bekor qiling", reply_markup=reply_markup)
        return POST_CONFIRMATION

    async def post_confirmation(self, update: Update, context: CallbackContext) -> int:
        user_input = update.message.text.strip()
        pending_post = context.user_data.get('pending_post')

        if user_input == "✅ Postni jo'natish" and pending_post:
            all_users = User.objects.values_list('chat_id', flat=True)
            for chat_id in all_users:
                try:
                    await context.bot.copy_message(
                        chat_id=chat_id,
                        from_chat_id=pending_post['chat_id'],
                        message_id=pending_post['message_id']

                    )
                except Exception as e:
                    print(f"Error sending message to chat id {
                          chat_id}. Error: {e}")
            await update.message.reply_text("Post barcha foydalanuvchilarga muvaffaqiyatli jo'natildi ✅")
            await update.message.reply_text("💼 Admin menu", reply_markup=ReplyKeyboardMarkup([[BOT_STATS], [USER_STATS], [START], [POST_MESSAGE]], resize_keyboard=True), parse_mode='HTML')

            context.user_data.pop('pending_post', None)
            return ADMIN_MENU_STATE

        elif user_input == "❌ Bekor qilish":
            await update.message.reply_text("Postni jo'natish bekor qilindi ❌", )
            await update.message.reply_text("💼 Admin menu", reply_markup=ReplyKeyboardMarkup([[BOT_STATS], [USER_STATS], [START], [POST_MESSAGE]], resize_keyboard=True), parse_mode='HTML')
            context.user_data.pop('pending_post', None)
            return ADMIN_MENU_STATE

        else:
            await update.message.reply_text("Iltimos, ✅ Postni jo'natish yoki ❌ Bekor qilish dan birini tanlang.")
            return POST_CONFIRMATION

    async def referral_menu(self, update: Update, context: CallbackContext) -> int:
        action = update.message.text.strip()

        if action == CREATE_REFERRAL_STATE:
            return await self.create_referral(update, context)
            # return REFERRAL_MENU

        # elif action == BACK:
        #     await self.admin_menu(update, context)
        #     return ADMIN_MENU_STATE

        # referrals = context.bot_data.get('referrals', {})
        # if action in referrals:
        #     context.user_data['selected_referral'] = action
        #     await self.handle_selected_referral(update, context)
        #     return REFERRAL_OPTIONS

        # referral_keyboard = [[CREATE_REFERRAL_STATE]] + [[code]
            #  for code in referrals.keys()] + [[BACK]]
        # reply_markup = ReplyKeyboardMarkup(
            # referral_keyboard, resize_keyboard=True, one_time_keyboard=True)

        # await update.message.reply_text("Select an option:", reply_markup=reply_markup)

        await update.message.reply_text("🔖  Referrallar", reply_markup=ReplyKeyboardMarkup([
            [CREATE_REFERRAL_STATE],
            *distribute([referral.name for referral in Referral.objects.all()]),
            [BACK]
        ], resize_keyboard=True, one_time_keyboard=True))

        return REFERRAL_MENU

    async def referral_select_referral(self, update: Update, context: CallbackContext):

        referral = Referral.objects.filter(name=update.message.text).first()

        if referral is None:
            await update.message.reply_text("REferral topilmadi.")
            return await self.referral_menu(update, context)

        context.user_data['selected_referral'] = referral.id

        await update.message.reply_text("Kerakli amaliyotni tanlang 👇", reply_markup=ReplyKeyboardMarkup([
            [
                DELETE_REFERRAL_STATE,

            ],
            [
                BACK
            ]
        ], resize_keyboard=True, one_time_keyboard=True))
        return REFERRAL_OPTIONS

    async def create_referral(self, update: Update, context: CallbackContext):

        # referral_code = ''.join(random.choices(
        #     string.ascii_uppercase + string.digits, k=6))

        # if 'referrals' not in context.bot_data:
        #     context.bot_data['referrals'] = {}

        # context.bot_data['referrals'][referral_code] = {
        #     "join_count": 0
        # }

        # bot_username = context.bot.username
        # referral_link = f"https://t.me/{bot_username}?start={referral_code}"

        # await update.message.reply_text(f"New referral link created: {referral_link}")
        # return REFERRAL_MENU

        await update.message.reply_text("Iltimos referralni nomini yuboring: ")
        return REFERRAL_CREATE_NAME

    async def create_referral_create_name_uz(self, update: Update, context: CallbackContext):

        Referral.objects.create(
            name=update.message.text
        )

        await update.message.reply_text("✅ Referral yaratildi")

        return await self.referral_menu(update, context)

    # async def handle_selected_referral(self, update: Update, context: CallbackContext) -> int:

    #     referral = Referral.objects.filter(name=update.message.text).first()

    #     if referral is None:
    #         await update.message.reply_text("Referral topilmadi", reply_markup=ReplyKeyboardMarkup([[BACK]], one_time_keyboard=True, resize_keyboard=True))
    #         return REFERRAL_MENU

    #     context.user_data['referral'] = referral.id

    #     await update.message.reply_text(
    #         f"Referral Code: {referral.name}\nJoin Count: {
    #             referral.users.count()}",
    #         reply_markup=ReplyKeyboardMarkup([
    #             [
    #                 [DELETE_REFERRAL_STATE]
    #             ],
    #             [BACK]
    #         ])
    #     )
    #     if update.message.text == DELETE_REFERRAL_STATE:
    #         await update.message.reply_text("Referral muvaffaqiyatli o'chirildi.")
    #         return REFERRAL_MENU
    #     return REFERRAL_MENU

        # referrals = context.bot_data.get('referrals', {})
        # referral_code = update.message.text.strip()

        # referrals = context.bot_data.get('referrals', {})
        # if referral_code in referrals:
        #     context.user_data['selected_referral'] = referral_code

        #     reply_markup = ReplyKeyboardMarkup(
        #         [[DELETE_REFERRAL_STATE, BACK]],
        #         resize_keyboard=True, one_time_keyboard=True
        #     )
        #     await update.message.reply_text(
        #         f"Referral Code: {referral_code}\nJoin Count: {
        #             referrals[referral_code]['join_count']}",
        #         reply_markup=reply_markup
        #     )
        # return REFERRAL_OPTIONS
        # elif referral_code == BACK:
        # return await self.referral_menu(update, context)
        # elif referral_code == DELETE_REFERRAL_STATE:
        # await update.message.reply_text("Sizning tanlagan referralingiz muvaffaqiyatli o'chirib yuborildi !", reply_markup=ReplyKeyboardMarkup([[BACK]], one_time_keyboard=True, resize_keyboard=True))
        # return REFERRAL_MENU
        # else:
        # await update.message.reply_text("Invalid option, please select from the menu.")
        # return REFERRAL_MENU

    async def delete_referral(self, update: Update, context: CallbackContext) -> int:
        # referral_code = context.user_data.get('selected_referral')
        # if referral_code and referral_code in context.bot_data['referrals']:
        #     del context.bot_data['referrals'][referral_code]
        #     await update.message.reply_text(f"Referral code {referral_code} deleted.")
        # else:
        #     await update.message.reply_text("Referral code not found.")

        referral = Referral.objects.filter(
            id=context.user_data['selected_referral']).first()

        referral.delete()

        await update.message.reply_text("Referral o'chirildi")

        return await self.referral_menu(update, context)

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
                    "ID": auto_increment_id if j == 1 else "",
                    "Ism": user.name if j == 1 else "",
                    "username": (f"@{user.username}" if user.username else "N/A") if j == 1 else "",
                    "user_chat_id": user.chat_id if j == 1 else "",
                    "Telefon raqami": user.phone_number if j == 1 else "",
                    "Ro'yxatdan o'tgan sana": user.registered_at.strftime("%d.%m.%Y %H:%M:%S"),
                    "Valyutadan": conv.currency.name if conv.direction == "TO_UZS" else "O'zbek so'mi",
                    "Valyutaga": "O'zbek so'mi" if conv.direction == "TO_UZS" else conv.currency.name,
                    "Kurs narxi": conv.currency.cb_price,
                    "Miqdori": conv.amount,
                    "Jami summa": conv.convert_sum,
                    "almashinuv vaqti": conv.convert_date.strftime("%d.%m.%Y %H:%M:%S"),
                })
                auto_increment_id += 1

        df = pd.DataFrame(data)

        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, index=False,
                    sheet_name='Foydalanuvchilar statistikasi')

        writer.close()
        output.seek(0)

        await context.bot.send_document(
            chat_id=update.message.chat_id,
            document=output,
            filename="foydalanuvchilar_statistikasi.xlsx",
        )

    def run(self):
        self.application.run_polling()

    async def sync_currencies(self, context: CallbackContext):

        sync_currencies()
