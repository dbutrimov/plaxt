from django.http import HttpResponse
from django.shortcuts import render
from django.views import View

from accounts.utils import hx_redirect
from common.models import PlexAccount
from plaxt import settings


class LinkView(View):
    http_method_names = ['get', 'delete']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return hx_redirect(settings.LOGIN_URL)

        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return render(request, 'link.html')

    def delete(self, request):
        user = request.user

        try:
            plex_account = user.plexaccount
        except PlexAccount.DoesNotExist:
            plex_account = None

        if plex_account:
            user.plexaccount = None
            user.save()
            plex_account.delete()

        if request.headers.get('X-ConfirmDialog'):
            return HttpResponse(status=204, headers={'HX-Trigger': 'linkChanged'})

        response = render(request, 'link.html')
        response.headers['HX-Trigger'] = 'linkChanged'

        return response
