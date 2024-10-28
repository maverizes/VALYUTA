import re
from telegram.ext.filters import MessageFilter, Text

from constants import BACK
from icecream import ic

# class ExcludeCommandsFilter(MessageFilter):
#     def filter(self, message):
#         res = not bool(re.match(rf"^(/start|/admin|{BACK})$", message.text))

#         return ic(res)


EXCLUDE = ~Text(["/start", "/admin", BACK])
