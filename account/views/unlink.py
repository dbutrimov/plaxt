from django.shortcuts import redirect
from django.views import View

from account.models import TraktAccount
from account.views import ACCOUNT_ID_KEY


class UnlinkView(View):
    http_method_names = ['post']

    def post(self, request):
        account_id = request.session.get(ACCOUNT_ID_KEY)
        if not account_id:
            return redirect('login')

        account = TraktAccount.objects.get(uuid=account_id)
        plex_account = account.plex_account
        if plex_account:
            account.plex_account = None
            account.save()

            plex_account.delete()

        return redirect('index')
