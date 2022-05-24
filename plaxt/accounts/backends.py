from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from trakt import Trakt

from common import utils
from common.models import TraktAccount, TraktAuth


class TraktBackend(BaseBackend):
    def authenticate(self, request, auth_code=None):
        auth_response = Trakt['oauth'].token_exchange(
            auth_code,
            utils.build_trakt_redirect_uri(request),
            exceptions=True,
        )

        if not auth_response:
            return None

        with Trakt.configuration.defaults.oauth.from_response(auth_response):
            user_settings = Trakt['users/settings'].get(exceptions=True)
            user = user_settings['user']
            user_id = user['ids']['uuid']
            username = user['username']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = User(username=username)
            user.save()

        try:
            trakt_account = TraktAccount.objects.get(pk=user.pk)
        except TraktAccount.DoesNotExist:
            trakt_account = TraktAccount(
                uuid=user_id,
                username=username,
                auth=TraktAuth(),
                user=user,
            )

        trakt_account.auth.from_response(auth_response)
        trakt_account.save()

        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
