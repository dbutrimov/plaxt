from django.core.exceptions import PermissionDenied
from django.core.validators import RegexValidator
from plexapi.myplex import MyPlexAccount
from rest_framework.request import Request as RestRequest
from rest_framework.response import Response as RestResponse
from rest_framework.views import APIView

from accounts.tasks import schedule_sync_task, logger
from common.models import PlexAccount, PlexServer


class ServersView(APIView):
    def get(self, request: RestRequest):
        user = request.user

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

        return RestResponse(servers)

    def put(self, request: RestRequest):
        user = request.user

        try:
            plex_account = user.plexaccount
        except PlexAccount.DoesNotExist:
            plex_account = None

        if not plex_account:
            return PermissionDenied()

        connection = request.data.get('connection')
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

        try:
            schedule_sync_task(user)
        except Exception as exc:
            logger.error(exc)

        return RestResponse({'success': True})
