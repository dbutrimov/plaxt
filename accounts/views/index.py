from django.shortcuts import redirect
from django.views.generic import TemplateView

from accounts.forms import LinkForm
from common.models.plex import PlexAccount
from plaxt import settings


class IndexView(TemplateView):
    template_name = "index.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'{settings.LOGIN_URL}?next={request.path}')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        request = self.request

        user = request.user
        try:
            plex_account = user.plexaccount
        except PlexAccount.DoesNotExist:
            plex_account = None

        link_form = LinkForm() if not plex_account else None

        context.update({
            'link_form': link_form,
        })

        return context
