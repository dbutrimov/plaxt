from django.middleware import csrf
from django.shortcuts import redirect
from django.views.generic import TemplateView

from accounts import settings
from common import trakt_utils


class LoginView(TemplateView):
    template_name = "login.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('index')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        request = self.request

        csrf_token = csrf.get_token(request)
        context.update({
            'action': 'https://trakt.tv/oauth/authorize',
            'client_id': settings.TRAKT_CLIENT,
            'redirect_uri': trakt_utils.build_trakt_redirect_uri(request),
            'response_type': 'code',
            'state': csrf_token,
        })

        return context
