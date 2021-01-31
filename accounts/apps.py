import logging

from django.apps import AppConfig
from trakt import Trakt

from . import settings

logger = logging.getLogger(__name__)


class AccountsConfig(AppConfig):
    name = 'accounts'

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

        from common.models import TraktAccount

        trakt_account = TraktAccount.objects.get(uuid=username)
        trakt_auth = trakt_account.auth
        trakt_auth.from_response(authorization)
        trakt_auth.save()
