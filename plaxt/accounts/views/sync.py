from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.views import View

from common.models import PlexAccount


class SyncView(View):
    http_method_names = ['get', 'delete']

    def get(self, request):
        return render(request, 'sync.html')

    def delete(self, request):
        user = request.user

        try:
            plex_account = user.plexaccount
        except PlexAccount.DoesNotExist:
            return Http404()

        plex_server = plex_account.server
        if plex_server:
            plex_account.server = None
            plex_account.save()
            plex_server.delete()

        if request.headers.get('X-ConfirmDialog'):
            return HttpResponse(status=204, headers={'HX-Trigger': 'syncChanged'})

        response = render(request, 'sync.html')
        response.headers['HX-Trigger'] = 'syncChanged'

        return response
