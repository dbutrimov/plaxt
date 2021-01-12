import logging

from django.apps import AppConfig
from trakt import Trakt

from . import settings

logger = logging.getLogger(__name__)


class AccountConfig(AppConfig):
    name = 'account'

    def ready(self):
        Trakt.configuration.defaults.client(
            id=settings.TRAKT_CLIENT,
            secret=settings.TRAKT_SECRET
        )

        Trakt.on('oauth.refresh', self.on_token_refresh)

    def on_token_refresh(self, username, authorization):
        # OAuth token refreshed, store authorization for future calls
        logger.info('Token refreshed - authorization: %r' % authorization)

        if not username:
            raise Exception('username is not defined')

        from account.models import TraktAccount

        account = TraktAccount.objects.get(username=username)
        auth = account.auth
        auth.from_response(authorization)
        auth.save()
