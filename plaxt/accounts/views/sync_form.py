from celery import states
from celery.result import AsyncResult
from django.shortcuts import render
from django.views import View

from accounts.tasks import sync_account_by_id
from accounts.utils import hx_redirect
from common.models import PlexAccount
from plaxt import settings


class SyncFormView(View):
    http_method_names = ['get', 'post']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return hx_redirect(settings.LOGIN_URL)

        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        user = request.user

        try:
            plex_account = user.plexaccount
        except PlexAccount.DoesNotExist:
            plex_account = None

        context = {'is_busy': False}
        if not plex_account:
            return render(request, 'sync_form.html', context)

        plex_server = plex_account.server
        if not plex_server:
            return render(request, 'sync_form.html', context)

        context['last_sync_at'] = plex_server.last_sync_at

        task_id = plex_server.last_task_id
        if not task_id:
            return render(request, 'sync_form.html', context)

        task_result = AsyncResult(task_id)

        is_busy = task_result.state not in states.READY_STATES
        context['is_busy'] = is_busy
        if is_busy:
            context['task_id'] = task_result.task_id

        return render(request, 'sync_form.html', context)

    def post(self, request):
        user = request.user

        try:
            plex_account = user.plexaccount
        except PlexAccount.DoesNotExist:
            plex_account = None

        context = {'is_busy': False}
        if not plex_account:
            return render(request, 'sync_form.html', context)

        plex_server = plex_account.server
        if not plex_server:
            return render(request, 'sync_form.html', context)

        last_sync_at = plex_server.last_sync_at

        task_id = plex_server.last_task_id
        if task_id:
            task_result = AsyncResult(task_id)
            if task_result.state not in states.READY_STATES:
                context = {
                    'is_busy': True,
                    'task_id': task_result.task_id,
                    'last_sync_at': last_sync_at,
                }

                return render(request, 'sync_form.html', context)

        task_result = sync_account_by_id.delay(request.user.id)
        plex_server.last_task_id = task_result.task_id
        plex_server.save()

        context = {
            'is_busy': True,
            'task_id': task_result.task_id,
            'last_sync_at': last_sync_at,
        }

        return render(request, 'sync_form.html', context)
