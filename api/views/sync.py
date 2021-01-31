from rest_framework.response import Response as RestRequest
from rest_framework.response import Response as RestResponse
from rest_framework.views import APIView

from accounts import tasks


class SyncView(APIView):
    def post(self, request: RestRequest):
        result = tasks.sync_account(request.user)
        return RestResponse(result)
