from datetime import datetime, timedelta, timezone
from typing import Optional

from celery import shared_task, states
from celery.result import AsyncResult
from celery.utils.log import get_task_logger
from django.contrib.auth.models import User
from django.db.models import Q

from accounts.adapters import PlexAdapter, TraktAdapter
from api.models import Movie, Show, Media, Episode, Season
from common.models import PlexAccount, PlexServer
from plaxt.celery import app

logger = get_task_logger(__name__)

ITEMS_LIMIT = 100


def get_history_timestamp(history: list[Media]) -> Optional[datetime]:
    result: Optional[datetime] = None
    for media in history:
        if isinstance(media, Movie):
            if not result or media.watched_at > result:
                result = media.watched_at

        if isinstance(media, Episode):
            if not result or media.watched_at > result:
                result = media.watched_at

        if isinstance(media, Season):
            for episode in media.episodes:
                if not result or episode.watched_at > result:
                    result = episode.watched_at

        if isinstance(media, Show):
            for season in media.seasons:
                for episode in season.episodes:
                    if not result or episode.watched_at > result:
                        result = episode.watched_at

        return result


def sync_account(user: User):
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

    plex_adapter = PlexAdapter(plex_account)

    trakt_account = user.traktaccount
    trakt_adapter = TraktAdapter(trakt_account)

    plex_timestamp = plex_server.plex_timestamp
    min_date = plex_timestamp.replace(microsecond=0) + timedelta(seconds=1) if plex_timestamp else None
    plex_history = plex_adapter.fetch(min_date=min_date, items_limit=ITEMS_LIMIT)
    history_timestamp = get_history_timestamp(plex_history)
    if history_timestamp and (not plex_timestamp or history_timestamp > plex_timestamp):
        plex_timestamp = history_timestamp

    trakt_result = trakt_adapter.push(plex_history)
    plex_server.plex_timestamp = plex_timestamp
    plex_server.save()

    trakt_timestamp = plex_server.trakt_timestamp
    min_date = trakt_timestamp.replace(microsecond=0) + timedelta(seconds=1) if trakt_timestamp else None
    trakt_history = trakt_adapter.fetch(min_date=min_date, items_limit=ITEMS_LIMIT)
    history_timestamp = get_history_timestamp(trakt_history)
    if history_timestamp and (not trakt_timestamp or history_timestamp > trakt_timestamp):
        trakt_timestamp = history_timestamp

    plex_result = plex_adapter.push(trakt_history)
    plex_server.trakt_timestamp = trakt_timestamp
    plex_server.save()

    plex_server.last_sync_at = datetime.now(tz=timezone.utc).replace(microsecond=0)
    plex_server.save()

    return {
        'trakt': trakt_result,
        'plex': plex_result,
    }


@shared_task(name='plaxt.accounts.sync_one')
def sync_account_by_id(uid: int):
    user = User.objects.get(pk=uid)
    return sync_account(user)


@app.task(name='plaxt.accounts.sync')
def sync():
    min_date = datetime.now(tz=timezone.utc).replace(microsecond=0) - timedelta(hours=3)
    servers = PlexServer.objects.filter(
        Q(connection__isnull=False) & (Q(last_sync_at__isnull=True) | Q(last_sync_at__lt=min_date))
    ).order_by('last_sync_at')

    uids = list()
    for server in servers:
        task_id = server.last_task_id
        if task_id:
            task_result = AsyncResult(task_id)
            if task_result.state not in states.READY_STATES:
                continue

        plex_account = PlexAccount.objects.get(server_id=server.id)
        uid = plex_account.user.id

        task_result = sync_account_by_id.delay(uid)
        server.last_task_id = task_result.task_id
        server.save()

        uids.append(uid)

    return uids


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        timedelta(hours=1),
        sync.s(),
    )
