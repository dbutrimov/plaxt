import json
import time
from datetime import datetime, timedelta, timezone

from celery import Task
from celery.utils.log import get_task_logger
from django.contrib.auth.models import User
from django_celery_beat.models import PeriodicTask, IntervalSchedule

from accounts.adapters import PlexAdapter, TraktAdapter
from api.models import Movie, Episode
from common.models import PlexAccount
from plaxt.celery import app

logger = get_task_logger(__name__)

ITEMS_LIMIT = 1000


def _filter_items(source, second):
    watch_troubleshoot = timedelta(hours=3)

    result = list()

    for item in source:
        if isinstance(item, Movie):
            exists = any(abs((x.watched_at - item.watched_at)) < watch_troubleshoot and
                         any(x.ids.get(key, None) == val for key, val in item.ids.items())
                         for x in second
                         if x.type == item.type)
            if not exists:
                result.append(item)

        if isinstance(item, Episode):
            exists = any(abs((x.watched_at - item.watched_at)) < watch_troubleshoot and
                         x.season == item.season and
                         x.number == item.number and
                         any(x.show.ids.get(key, None) == val for key, val in item.show.ids.items())
                         for x in second
                         if x.type == item.type)
            if not exists:
                result.append(item)

    return result


def sync_account(task: Task, user: User):
    try:
        plex_account = user.plexaccount
    except PlexAccount.DoesNotExist:
        plex_account = None

    if not plex_account:
        return {
            'detail': 'Reject: Plex was not linked',
        }

    plex_server = plex_account.server
    if not plex_server:
        return {
            'detail': 'Reject: Server was not setup',
        }

    plex_server.sync_task_id = task.request.id
    plex_server.save()

    now = datetime.now(tz=timezone.utc)
    min_date = now - timedelta(days=120)
    sync_at = datetime(2020, 1, 1, tzinfo=timezone.utc)  # plex_server.sync_at
    if sync_at and sync_at > min_date:
        min_date = sync_at.astimezone(timezone.utc)

    plex_adapter = PlexAdapter(plex_account, min_date)
    plex_adapter.items_limit = ITEMS_LIMIT

    trakt_account = user.traktaccount
    trakt_adapter = TraktAdapter(trakt_account, min_date)
    trakt_adapter.items_limit = ITEMS_LIMIT

    plex_fetch = plex_adapter.fetch()
    trakt_fetch = trakt_adapter.fetch()

    trakt_push = _filter_items(plex_fetch, trakt_fetch)
    plex_push = _filter_items(trakt_fetch, plex_fetch)

    plex_push = plex_adapter.push(plex_push)
    trakt_push = trakt_adapter.push(trakt_push)

    plex_server.sync_at = now
    plex_server.save()

    return {
        'plex': plex_push,
        'trakt': trakt_push,
    }


@app.task(bind=True, name='sync_account')
def sync_account_by_id(self: Task, uid):
    user = User.objects.get(pk=uid)
    return sync_account(self, user)


# @app.task
# def sync():
#     result = {}
#     for user in User.objects.all():
#         try:
#             sleep(5)
#             result[user.username] = sync_account(user)
#         except Exception as exc:
#             exc_type = type(exc)
#             result[user.username] = {
#                 'type': f'{exc_type.__module__}.{exc_type.__name__}',
#                 'detail': str(exc),
#             }
#
#     return result


# @app.on_after_finalize.connect
# def setup_periodic_tasks(sender, **kwargs):
#     sender.add_periodic_task(10.0, sync.s())
#     pass


def schedule_sync_task(user):
    task_name = f'sync_user_{user.pk}'

    schedule, created = IntervalSchedule.objects.get_or_create(
        every=10,
        period=IntervalSchedule.SECONDS,
    )

    sync_task = PeriodicTask.objects.update_or_create(
        task='sync_account',
        name=task_name,
        defaults=dict(
            interval=schedule,
            expire_seconds=60,  # If not run within 60 seconds, forget it; another one will be scheduled soon.
            args=json.dumps((user.pk,)),
        ),
    )

    try:
        plex_account = user.plexaccount
    except PlexAccount.DoesNotExist:
        plex_account = None

    plex_server = plex_account.server if plex_account else None

    sync_task.enabled = plex_server is not None
    sync_task.save()
