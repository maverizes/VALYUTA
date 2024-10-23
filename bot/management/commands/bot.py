import os
from django.core.management.base import BaseCommand

from tg_bot import Bot

class Command(BaseCommand):
    def handle(self, *args, **options):
        TOKEN = os.getenv("BOT_TOKEN_API")
        bot = Bot(TOKEN)
        bot.run()