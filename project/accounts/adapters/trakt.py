from datetime import timezone, timedelta
from typing import List, Optional

from trakt import Trakt
from trakt.objects import Movie as TraktMovie, Episode as TraktEpisode

from api.models import Media, Movie, Show, Episode
from . import Adapter
from ..models import TraktHistoryMovie, TraktHistoryShow, TraktHistorySeason, TraktHistoryEpisode


class TraktAdapter(Adapter):
    def __init__(self, trakt_account, min_date):
        self.trakt_account = trakt_account
        self.min_date = min_date
        self.items_limit = 1000

    def fetch(self) -> Optional[List[Media]]:
        trakt_auth = self.trakt_account.auth
        authentication = Trakt.configuration.defaults.oauth.from_response(
            response=trakt_auth.to_response(),
            refresh=True,
            username=self.trakt_account.uuid,
        )

        result = list()
        with authentication:
            history = list(Trakt['sync/history'].get(
                start_at=self.min_date,
                per_page=self.items_limit,
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
                    season, number = history_item.pk
                    item_show = history_item.show

                    show = Show(
                        ids=dict(item_show.keys),
                        title=item_show.title,
                        year=item_show.year,
                    )

                    episode = Episode(
                        ids=dict([(key, value) for (key, value) in history_item.keys[1:]]),
                        title=history_item.title,
                        season=season,
                        number=number,
                        watched_at=watched_at,
                        show=show,
                    )

                    result.append(episode)
                    continue

        return result

    def push(self, items: List[Media]):
        watch_troubleshoot = timedelta(hours=0.5)

        movies = list()
        shows = list()

        for item in items:
            if isinstance(item, Movie):
                movies.append(
                    TraktHistoryMovie(
                        ids=item.ids,
                        title=item.title,
                        year=item.year,
                        watched_at=item.watched_at,
                    ))
                continue

            if isinstance(item, Episode):
                item_show = item.show

                show = next(
                    (x for x in shows
                     if any(x.ids.get(key, None) == val for key, val in item_show.ids.items())),
                    None)

                if not show:
                    show = TraktHistoryShow(
                        ids=item_show.ids,
                        title=item_show.title,
                        year=item_show.year,
                    )
                    shows.append(show)

                seasons = show.seasons
                season = next(
                    (x for x in seasons
                     if x.number == item.season),
                    None)

                if not season:
                    season = TraktHistorySeason(
                        number=item.season,
                    )
                    seasons.append(season)

                episodes = season.episodes
                episode = next(
                    (x for x in episodes
                     if x.number == item.number and abs(x.watched_at - item.watched_at) < watch_troubleshoot),
                    None)

                if not episode:
                    episode = TraktHistoryEpisode(
                        number=item.number,
                        watched_at=item.watched_at,
                    )
                    episodes.append(episode)

                continue

        if len(movies) <= 0 and len(shows) <= 0:
            return 'no data to push'

        items = {
            'movies': [movie.to_json() for movie in movies],
            'shows': [show.to_json() for show in shows],
        }

        trakt_auth = self.trakt_account.auth
        authentication = Trakt.configuration.defaults.oauth.from_response(
            response=trakt_auth.to_response(),
            refresh=True,
            username=self.trakt_account.uuid,
        )

        with authentication:
            return Trakt['sync/history'].add(items, exceptions=True)
