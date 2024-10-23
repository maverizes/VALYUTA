import re
from constants import UZBEK_PHONE_REGEX

phone_number = '+998907887170'

is_match = re.match(UZBEK_PHONE_REGEX, phone_number)

print(is_match)



