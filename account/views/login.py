from django.middleware import csrf
from django.shortcuts import redirect
from django.views.generic import TemplateView

from account import settings
from account.views import ACCOUNT_ID_KEY, build_trakt_redirect_uri


class LoginView(TemplateView):
    template_name = "login.html"

    def dispatch(self, request, *args, **kwargs):
        account_id = request.session.get(ACCOUNT_ID_KEY)
        if account_id:
            return redirect('index')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        request = self.request

        csrf_token = csrf.get_token(request)
        context.update({
            'action': 'https://trakt.tv/oauth/authorize',
            'client_id': settings.TRAKT_CLIENT,
            'redirect_uri': build_trakt_redirect_uri(request),
            'response_type': 'code',
            'state': csrf_token,
        })

        return context
