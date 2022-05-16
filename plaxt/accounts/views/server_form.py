from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.views import View

from accounts.forms.server_form import ServerForm
from accounts.utils import hx_redirect
from common.models import PlexAccount, PlexServer
from plaxt import settings


class ServerFormView(View):
    http_method_names = ['get', 'post']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return hx_redirect(settings.LOGIN_URL)

        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        user = request.user

        try:
            plex_account = user.plexaccount
        except PlexAccount.DoesNotExist:
            return Http404()

        plex_server = plex_account.server
        address = plex_server.connection if plex_server else None

        form = ServerForm(initial={'address': address})
        return render(request, 'server_form.html', {'form': form})

    def post(self, request):
        user = request.user

        form = ServerForm(request.POST)
        if not form.is_valid():
            return render(request, 'server_form.html', {'form': form})

        address = form.cleaned_data['address']

        try:
            plex_account = user.plexaccount
        except PlexAccount.DoesNotExist:
            return Http404()

        plex_server = plex_account.server

        if not plex_server:
            plex_account.server = PlexServer(connection=address)
            plex_account.save()
        else:
            plex_server.connection = address
            plex_server.save()

        return HttpResponse(status=204, headers={'HX-Trigger': 'serverChanged'})
