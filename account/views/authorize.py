from django.core.exceptions import PermissionDenied
from django.middleware import csrf
from django.shortcuts import redirect
from django.views import View
from trakt import Trakt

from account.models import TraktAccount, TraktAuth
from account.views import build_trakt_redirect_uri, ACCOUNT_ID_KEY


class AuthorizeView(View):
    http_method_names = ['get']

    def get(self, request):
        auth_code = request.GET['code']
        state = request.GET['state']

        csrf_token = csrf.get_token(request)
        request_csrf_token = csrf._sanitize_token(state)
        if not csrf._compare_masked_tokens(request_csrf_token, csrf_token):
            raise PermissionDenied()

        auth_response = Trakt['oauth'].token_exchange(auth_code, build_trakt_redirect_uri(request))
        if not auth_response:
            raise Exception()

        with Trakt.configuration.defaults.oauth.from_response(auth_response):
            user_settings = Trakt['users/settings'].get()
            user = user_settings['user']
            user_id = user['ids']['uuid']
            username = user['username']

        account = TraktAccount.objects.filter(uuid=user_id).first()
        if not account:
            account = TraktAccount(
                uuid=user_id,
                username=username,
                auth=TraktAuth(),
            )
        else:
            account.username = username

        auth = account.auth
        if not auth:
            auth = TraktAuth()
            account.auth = auth

        auth.from_response(auth_response)

        auth.save()
        account.save()

        request.session[ACCOUNT_ID_KEY] = account.uuid

        return redirect('index')
