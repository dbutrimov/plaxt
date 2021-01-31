from django.core.exceptions import PermissionDenied
from django.core.validators import RegexValidator
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from plexapi.myplex import MyPlexAccount

from common.models.plex import PlexAccount, PlexServer


@method_decorator(csrf_exempt, name='dispatch')
class ServersView(View):
    http_method_names = ['get', 'post']

    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return PermissionDenied()

        try:
            plex_account = user.plexaccount
        except PlexAccount.DoesNotExist:
            plex_account = None

        servers = []
        if plex_account:
            plex = MyPlexAccount(plex_account.username, token=plex_account.token)
            devices = plex.devices()
            servers = [{
                'name': x.name,
                'connections': x.connections,
            } for x in devices if x.provides.lower() == 'server']

        return JsonResponse(servers, safe=False)

    def post(self, request):
        user = request.user
        if not user.is_authenticated:
            return PermissionDenied()

        try:
            plex_account = user.plexaccount
        except PlexAccount.DoesNotExist:
            plex_account = None

        if not plex_account:
            return PermissionDenied()

        connection = request.POST.get('address')
        if connection:
            validate = RegexValidator(r'^https?:\/\/[^:/]+(:\d+)?\/?$')
            validate(connection)

        plex_server = plex_account.server
        if plex_server and (not connection or plex_server.connection != connection):
            plex_account.server = None
            plex_account.save()
            plex_server.delete()
            plex_server = None

        if connection:
            if not plex_server:
                plex_account.server = PlexServer(connection=connection)
                plex_account.save()
            else:
                plex_server.connection = connection
                plex_server.save()

        return JsonResponse({'success': True})
