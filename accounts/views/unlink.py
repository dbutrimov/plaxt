from django.shortcuts import redirect
from django.views import View

from common.models.plex import PlexAccount
from plaxt import settings


class UnlinkView(View):
    http_method_names = ['post']

    def post(self, request):
        user = request.user
        if not request.user.is_authenticated:
            return redirect(f'{settings.LOGIN_URL}?next={request.path}')

        try:
            plex_account = user.plexaccount
        except PlexAccount.DoesNotExist:
            plex_account = None

        if plex_account:
            user.plexaccount = None
            user.save()
            plex_account.delete()

        return redirect('index')
