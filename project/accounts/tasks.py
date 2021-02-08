import json
import time
from datetime import datetime, timedelta, timezone

from celery import Task
from celery.utils.log import get_task_logger
from django.contrib.auth.models import User
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from plexapi.server import PlexServer
from trakt import Trakt
from trakt.objects import Movie as TraktMovie, Episode as TraktEpisode

from common import utils
from common.models import PlexAccount
from plaxt.celery import app

logger = get_task_logger(__name__)


def _fetch_plex(plex_account, min_date):
    plex_server = plex_account.server
    if not plex_server:
        return None

    shows_cache = dict()
    result = list()

    plex = PlexServer(plex_server.connection, plex_account.token)
    sections = plex.library.sections()
    for section in sections:
        history = section.history(mindate=min_date)
        for item in history:
            item.reload()

            is_watched = item.isWatched
            if not is_watched:
                continue

            watched_at = item.lastViewedAt.astimezone(timezone.utc)

            if item.type == 'movie':
                result.append({
                    'type': item.type,
                    'ids': utils.parse_ids(item.guid),
                    'title': item.title,
                    'year': item.year,
                    'watched_at': watched_at,
                })

                continue

            if item.type == 'episode':
                show_key = item.grandparentKey
                if show_key in shows_cache:
                    show = shows_cache[show_key]
                else:
                    show_item = plex.library.fetchItem(show_key)
                    show = {
                        'ids': utils.parse_ids(show_item.guid),
                        'title': show_item.title,
                        'year': show_item.year,
                    }
                    shows_cache[show_key] = show

                season = int(item.parentIndex)
                number = int(item.index)
                result.append({
                    'type': item.type,
                    'season': season,
                    'number': number,
                    'watched_at': watched_at,
                    'show': show,
                })

                continue

    return result


def _fetch_trakt(trakt_account, min_date):
    trakt_auth = trakt_account.auth
    authentication = Trakt.configuration.defaults.oauth.from_response(
        response=trakt_auth.to_response(),
        refresh=True,
        username=trakt_account.uuid,
    )

    result = list()
    with authentication:
        # result = Trakt['sync/history'].add(items, exceptions=True)
        history = list(Trakt['sync/history'].get(start_at=min_date, exceptions=True))
        for history_item in history:
            watched_at = history_item.watched_at.astimezone(timezone.utc)

            if isinstance(history_item, TraktMovie):
                result.append({
                    'type': 'movie',
                    'ids': dict(history_item.keys),
                    'title': history_item.title,
                    'year': history_item.year,
                    'watched_at': watched_at,
                })

                continue

            if isinstance(history_item, TraktEpisode):
                season, number = history_item.pk
                show = history_item.show
                result.append({
                    'type': 'episode',
                    'ids': dict([(key, value) for (key, value) in history_item.keys[1:]]),
                    'season': season,
                    'number': number,
                    'title': history_item.title,
                    'watched_at': watched_at,
                    'show': {
                        'ids': dict(show.keys),
                        'title': show.title,
                        'year': show.year,
                    },
                })

                continue

    return result


def _filter_items(source, second):
    watch_troubleshoot = 1800  # 30 min

    result = list()

    for item in source:
        item_type = item['type']
        if item_type == 'movie':
            exists = any(abs((x['watched_at'] - item['watched_at']).total_seconds()) < watch_troubleshoot and
                         any(x['ids'].get(key, None) == val for key, val in item['ids'].items())
                         for x in second
                         if x['type'] == item_type)
            if not exists:
                result.append(item)

        if item_type == 'episode':
            exists = any(abs((x['watched_at'] - item['watched_at']).total_seconds()) < watch_troubleshoot and
                         x['season'] == item['season'] and
                         x['number'] == item['number'] and
                         any(x['show']['ids'].get(key, None) == val for key, val in item['show']['ids'].items())
                         for x in second
                         if x['type'] == item_type)
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

    time.sleep(5)

    now = datetime.now(tz=timezone.utc)
    min_date = now - timedelta(days=60)
    sync_at = plex_server.sync_at
    if sync_at and sync_at > min_date:
        min_date = sync_at.astimezone(timezone.utc)

    plex_fetch = _fetch_plex(plex_account, min_date)

    trakt_account = user.traktaccount
    trakt_fetch = _fetch_trakt(trakt_account, min_date)

    trakt_push = _filter_items(plex_fetch, trakt_fetch)
    plex_push = _filter_items(trakt_fetch, plex_fetch)

    # todo: push here

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
