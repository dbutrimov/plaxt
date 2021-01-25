from django.shortcuts import redirect
from django.views import View

from account.models import TraktAccount
from account.views import ACCOUNT_ID_KEY


class DeleteView(View):
    http_method_names = ['post']

    def post(self, request):
        account_id = request.session.get(ACCOUNT_ID_KEY)
        if not account_id:
            return redirect('login')

        try:
            del request.session[ACCOUNT_ID_KEY]
        except KeyError:
            pass

        account = TraktAccount.objects.get(uuid=account_id)
        account.delete()

        return redirect('index')
