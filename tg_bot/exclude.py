import re
from telegram.ext.filters import MessageFilter


class ExcludeCommandsFilter(MessageFilter):
    def filter(self, message):
        return not bool(re.match(r"^/(start|admin)$", message.text))


EXCLUDE = ExcludeCommandsFilter()
