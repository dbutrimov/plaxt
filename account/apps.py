from django.apps import AppConfig
from trakt import Trakt

from . import settings


class AccountConfig(AppConfig):
    name = 'account'

    def ready(self):
        Trakt.configuration.defaults.client(
            id=settings.TRAKT_CLIENT,
            secret=settings.TRAKT_SECRET
        )
