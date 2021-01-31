import logging
from datetime import datetime, timedelta

from celery import shared_task
from plexapi.server import PlexServer
from trakt import Trakt

from common import utils
from common.models import TraktAccount

# logger = get_task_logger(__name__)
logger = logging.getLogger(__name__)


def sync_account(account):
    plex_account = account.plex_account
    if not plex_account:
        logger.info(f'[{account.name}] Plex was not linked - skip')
        return

    server = plex_account.server
    if not server:
        logger.info(f'[{account.name}] Server was not setup - skip')
        return

    min_date = datetime.utcnow() - timedelta(days=14)  # server.sync_at

    movies = dict()
    shows = dict()

    plex = PlexServer(server.connection, plex_account.token)
    sections = plex.library.sections()
    for section in sections:
        history = section.history(mindate=min_date)
        for item in history:
            item.reload()

            is_watched = item.isWatched
            if not is_watched:
                continue

            watched_at = item.lastViewedAt

            if item.type == 'movie':
                movie_key = item.key
                if movie_key not in movies:
                    movie = {
                        'watched_at': watched_at.isoformat(),
                        'title': item.title,
                        'year': item.year,
                        'ids': utils.parse_ids(item.guid),
                    }
                    movies[movie_key] = movie

                continue

            if item.type == 'episode':
                show_key = item.grandparentKey
                if show_key in shows:
                    show = shows[show_key]
                else:
                    show_item = plex.library.fetchItem(show_key)
                    show = {
                        'title': show_item.title,
                        'year': show_item.year,
                        'ids': utils.parse_ids(show_item.guid),
                        'seasons': list(),
                    }
                    shows[show_key] = show

                seasons = show['seasons']
                season_number = int(item.parentIndex)
                season = next((x for x in seasons if x['number'] == season_number), None)
                if not season:
                    season = {
                        'number': season_number,
                        'episodes': list(),
                    }
                    seasons.append(season)

                episodes = season['episodes']
                episode_number = int(item.index)
                episode = next((x for x in episodes if x['number'] == episode_number), None)
                if not episode:
                    episode = {
                        'watched_at': watched_at.isoformat(),
                        'number': episode_number,
                    }
                    episodes.append(episode)

                continue

    trakt_auth = account.auth
    authentication = Trakt.configuration.defaults.oauth.from_response(
        response=trakt_auth.to_response(),
        refresh=True,
        username=account.uuid,
    )

    items = {
        'movies': list(movies.values()),
        'shows': list(shows.values()),
    }

    with authentication:
        # result = Trakt['sync/history'].add(items, exceptions=True)
        history = list(Trakt['sync/history'].get(start_at=min_date, exceptions=True))
        result = [x.to_dict() for x in history]

    return {
        'plex': items,
        'trakt': result,
    }


@shared_task
def sync():
    result = {}
    for account in TraktAccount.objects.all():
        result[account.uuid] = sync_account(account)

    return result
