from typing import TYPE_CHECKING

import random
import string
from django.db import models


if TYPE_CHECKING:
    from user.models import User


def generate_code(length=7):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


class Referral(models.Model):

    name = models.CharField(max_length=255)

    code = models.CharField(max_length=7, default=generate_code)

    users: models.QuerySet["User"]
