from celery.result import AsyncResult
from rest_framework.request import Request as RestRequest
from rest_framework.response import Response as RestResponse
from rest_framework.views import APIView

from common.models import PlexAccount


class SyncView(APIView):
    def post(self, request: RestRequest):
        # result = tasks.sync_account(request.user)
        return RestResponse(None)


class SyncStatusView(APIView):
    def get(self, request: RestRequest):
        try:
            plex_account = request.user.plexaccount
        except PlexAccount.DoesNotExist:
            plex_account = None

        result = {'status': 'UNKNOWN'}
        if plex_account:
            plex_server = plex_account.server
            if plex_server:
                sync_task_id = plex_server.sync_task_id
                if sync_task_id:
                    task_result = AsyncResult(sync_task_id)
                    task_status = task_result.status
                    result.update({
                        'status': task_status,
                        'task_id': task_result.id,
                        'task_name': task_result.name,
                        'done_at': task_result.date_done,
                    })

                    if task_status == 'SUCCESS':
                        result.update({
                            'result': task_result.result,
                        })

        return RestResponse(result)
