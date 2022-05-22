from django.http import Http404
from django.shortcuts import render
from django.views import View
from plexapi.myplex import MyPlexAccount

from common.models import PlexAccount


class ServersView(View):
    http_method_names = ['get']

    def get(self, request):
        user = request.user

        try:
            plex_account = user.plexaccount
        except PlexAccount.DoesNotExist:
            return Http404()

        plex = MyPlexAccount(plex_account.username, token=plex_account.token)
        devices = plex.devices()
        servers = [{
            'name': x.name,
            'connections': x.connections,
        } for x in devices if x.provides.lower() == 'server']

        return render(request, 'servers.html', {'servers': servers})
