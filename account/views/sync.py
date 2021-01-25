from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from account import tasks


@method_decorator(csrf_exempt, name='dispatch')
class SyncView(View):
    http_method_names = ['get']

    def get(self, request):
        result = tasks.sync()
        return JsonResponse(result)
