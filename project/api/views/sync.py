from celery.result import AsyncResult
from celery.states import state
from rest_framework.request import Request as RestRequest
from rest_framework.response import Response as RestResponse
from rest_framework.views import APIView

from accounts.tasks import sync_account_by_id
from common.models import PlexAccount


def _prepare_response_data(task_result: AsyncResult):
    return {
        'status': task_result.status,
        'task_id': task_result.id,
        'done_at': task_result.date_done,
    }


class SyncView(APIView):
    def post(self, request: RestRequest):
        server = request.user.plexaccount.server
        task_id = server.last_task_id
        if task_id:
            task_result = AsyncResult(task_id)
            if state(task_result.status) < state(None):
                return RestResponse(_prepare_response_data(task_result))

        task_result = sync_account_by_id.delay(request.user.id)
        server.last_task_id = task_result.task_id
        server.save()

        return RestResponse(_prepare_response_data(task_result))


class SyncStatusView(APIView):
    def get(self, request: RestRequest):
        try:
            plex_account = request.user.plexaccount
        except PlexAccount.DoesNotExist:
            plex_account = None

        result = {'status': None}
        if plex_account:
            plex_server = plex_account.server
            if plex_server:
                sync_task_id = plex_server.last_task_id
                if sync_task_id:
                    task_result = AsyncResult(sync_task_id)
                    result = _prepare_response_data(task_result)

        return RestResponse(result)
