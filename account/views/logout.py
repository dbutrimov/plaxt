from django.shortcuts import redirect
from django.views import View

from account.views import ACCOUNT_ID_KEY


class LogoutView(View):
    http_method_names = ['post']

    def post(self, request):
        try:
            del request.session[ACCOUNT_ID_KEY]
        except KeyError:
            pass

        return redirect('index')
