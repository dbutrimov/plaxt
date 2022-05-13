from datetime import timezone, datetime, timedelta
from typing import List, Optional, Any

from trakt import Trakt
from trakt.objects import Movie as TraktMovie, Episode as TraktEpisode

from api.models import Media, Movie, Show, Episode, Season
from common.utils import find_trakt_media_id
from . import Adapter


class TraktAdapter(Adapter):
    def __init__(self, trakt_account):
        self.trakt_account = trakt_account

    def fetch(self, min_date: datetime = None, items_limit: int = 1000) -> Optional[List[Media]]:
        trakt_auth = self.trakt_account.auth
        authentication = Trakt.configuration.defaults.oauth.from_response(
            response=trakt_auth.to_response(),
            refresh=True,
            username=self.trakt_account.uuid,
        )

        result = list()
        shows = dict()

        with authentication:
            history = list(Trakt['sync/history'].get(
                start_at=min_date,
                per_page=items_limit,
                exceptions=True,
            ))

            for history_item in history:
                watched_at = history_item.watched_at.astimezone(timezone.utc)

                if isinstance(history_item, TraktMovie):
                    movie = Movie(
                        ids=dict(history_item.keys),
                        title=history_item.title,
                        year=history_item.year,
                        watched_at=watched_at,
                    )

                    result.append(movie)
                    continue

                if isinstance(history_item, TraktEpisode):
                    season_number, episode_number = history_item.pk
                    item_show = history_item.show

                    _, show_key = item_show.pk
                    if show_key in shows:
                        show = shows[show_key]
                    else:
                        show = Show(
                            ids=dict(item_show.keys),
                            title=item_show.title,
                            year=item_show.year,
                        )

                        shows[show_key] = show
                        result.append(show)

                    season = next((x for x in show.seasons if x.number == season_number), None)
                    if not season:
                        season = Season(
                            number=season_number,
                        )

                        show.seasons.append(season)

                    episode = Episode(
                        ids=dict([(key, value) for (key, value) in history_item.keys[1:]]),
                        title=history_item.title,
                        number=episode_number,
                        watched_at=watched_at,
                    )

                    season.episodes.append(episode)
                    continue

        return result

    def push(self, items: List[Media]) -> Optional[Any]:
        trakt_auth = self.trakt_account.auth
        authentication = Trakt.configuration.defaults.oauth.from_response(
            response=trakt_auth.to_response(),
            refresh=True,
            username=self.trakt_account.uuid,
        )

        with authentication:
            watch_troubleshoot = timedelta(minutes=30)

            movies = list()
            shows = list()

            for item in items:
                if isinstance(item, Movie):
                    movie_key = find_trakt_media_id(item.ids, 'movie')
                    if movie_key:
                        start_at = item.watched_at - watch_troubleshoot
                        end_at = item.watched_at + watch_troubleshoot

                        history = Trakt['sync/history'].movies(
                            id=movie_key,
                            start_at=start_at,
                            end_at=end_at,
                            exceptions=False,
                        )

                        if history and next(history, None) is not None:
                            continue

                    movies.append({
                        'ids': item.ids,
                        'title': item.title,
                        'year': item.year,
                        'watched_at': item.watched_at.isoformat(),
                    })

                    continue

                if isinstance(item, Show):
                    show_key = find_trakt_media_id(item.ids, 'show')

                    seasons = list()
                    for season in item.seasons:
                        episodes = list()
                        for episode in season.episodes:
                            if show_key:
                                start_at = episode.watched_at - watch_troubleshoot
                                end_at = episode.watched_at + watch_troubleshoot

                                history = Trakt['sync/history'].episodes(
                                    id=show_key,
                                    start_at=start_at,
                                    end_at=end_at,
                                    exceptions=False,
                                )

                                if history:
                                    trakt_episode = next(
                                        (x for x in history
                                         if x.pk[0] == season.number and x.pk[1] == episode.number),
                                        None)
                                    if trakt_episode:
                                        continue

                            episodes.append({
                                'number': episode.number,
                                'watched_at': episode.watched_at.isoformat(),
                            })

                        if len(episodes) > 0:
                            seasons.append({
                                'number': season.number,
                                'episodes': episodes,
                            })

                    if len(seasons) > 0:
                        shows.append({
                            'ids': item.ids,
                            'title': item.title,
                            'year': item.year,
                            'seasons': seasons,
                        })

                    continue

            if len(movies) <= 0 and len(shows) <= 0:
                return {
                    'message': 'Up-to-date',
                }

            items = {
                'movies': movies,
                'shows': shows,
            }

            return Trakt['sync/history'].add(items, exceptions=True)
