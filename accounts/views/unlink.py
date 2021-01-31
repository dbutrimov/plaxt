from django.shortcuts import redirect
from django.views import View

from common.models import PlexAccount
from plaxt import settings


class UnlinkView(View):
    http_method_names = ['post']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)

        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        user = request.user

        try:
            plex_account = user.plexaccount
        except PlexAccount.DoesNotExist:
            plex_account = None

        if plex_account:
            user.plexaccount = None
            user.save()
            plex_account.delete()

        return redirect('index')
