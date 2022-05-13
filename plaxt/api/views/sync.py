from celery import states
from celery.result import AsyncResult
from rest_framework.request import Request as RestRequest
from rest_framework.response import Response as RestResponse
from rest_framework.views import APIView

from accounts.tasks import sync_account_by_id
from common.models import PlexAccount


class SyncView(APIView):
    def post(self, request: RestRequest):
        plex_server = request.user.plexaccount.server
        last_sync_at = plex_server.last_sync_at

        task_id = plex_server.last_task_id
        if task_id:
            task_result = AsyncResult(task_id)
            if task_result.state not in states.READY_STATES:
                data = {
                    'is_busy': True,
                    'task_id': task_result.task_id,
                    'last_sync_at': last_sync_at,
                }

                return RestResponse(data)

        task_result = sync_account_by_id.delay(request.user.id)
        plex_server.last_task_id = task_result.task_id
        plex_server.save()

        data = {
            'is_busy': True,
            'task_id': task_result.task_id,
            'last_sync_at': last_sync_at,
        }

        return RestResponse(data)


class SyncStateView(APIView):
    def get(self, request: RestRequest):
        try:
            plex_account = request.user.plexaccount
        except PlexAccount.DoesNotExist:
            plex_account = None

        data = {'is_busy': False}
        if not plex_account:
            return RestResponse(data)

        plex_server = plex_account.server
        if not plex_server:
            return RestResponse(data)

        data['last_sync_at'] = plex_server.last_sync_at

        task_id = plex_server.last_task_id
        if not task_id:
            return RestResponse(data)

        task_result = AsyncResult(task_id)

        is_busy = task_result.state not in states.READY_STATES
        data['is_busy'] = is_busy
        if is_busy:
            data['task_id'] = task_result.task_id

        return RestResponse(data)
