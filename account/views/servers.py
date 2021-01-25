from django.core.exceptions import PermissionDenied
from django.core.validators import RegexValidator
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from plexapi.myplex import MyPlexAccount

from account.models import TraktAccount, PlexServer
from account.views import ACCOUNT_ID_KEY


@method_decorator(csrf_exempt, name='dispatch')
class ServersView(View):
    http_method_names = ['get', 'post']

    def get(self, request):
        account_id = request.session.get(ACCOUNT_ID_KEY)
        if not account_id:
            return PermissionDenied()

        account = TraktAccount.objects.get(uuid=account_id)
        db_plex_account = account.plex_account

        servers = []
        if db_plex_account:
            plex_account = MyPlexAccount(db_plex_account.username, token=db_plex_account.token)
            devices = plex_account.devices()
            servers = [{
                'name': x.name,
                'connections': x.connections,
            } for x in devices if x.provides.lower() == 'server']

        return JsonResponse(servers, safe=False)

    def post(self, request):
        account_id = request.session.get(ACCOUNT_ID_KEY)
        if not account_id:
            return PermissionDenied()

        account = TraktAccount.objects.get(uuid=account_id)
        db_plex_account = account.plex_account
        if not db_plex_account:
            return JsonResponse({'success': False})

        connection = request.POST.get('address')
        if connection:
            validate = RegexValidator(r'^https?:\/\/[^:/]+(:\d+)?\/?$')
            validate(connection)

        server = db_plex_account.server
        if server and (not connection or server.connection != connection):
            db_plex_account.server = None
            db_plex_account.save()
            server.delete()
            server = None

        if connection:
            if not server:
                server = PlexServer(connection=connection)
                server.save()
                db_plex_account.server = server
                db_plex_account.save()
            else:
                server.connection = connection
                server.save()

        return JsonResponse({'success': True})
