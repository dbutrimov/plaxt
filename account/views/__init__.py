import logging

from django.http import HttpRequest
from django.urls import reverse
from trakt import Trakt

from account.models import TraktAccount

logger = logging.getLogger(__name__)

ACCOUNT_ID_KEY = 'account_id'


def authenticate_trakt(account_id: str):
    account = TraktAccount.objects.get(uuid=account_id)
    auth = account.auth

    return Trakt.configuration.defaults.oauth.from_response(
        response=auth.to_response(),
        refresh=True,
        username=account_id,
    )


def build_trakt_redirect_uri(request: HttpRequest):
    return request.build_absolute_uri(reverse('authorize'))


def build_webhook_uri(request: HttpRequest, account_id):
    return '{0}?id={1}'.format(request.build_absolute_uri('/webhook'), account_id)
