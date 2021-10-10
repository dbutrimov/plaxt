from datetime import timezone
from typing import List, Optional

from plexapi.exceptions import Unsupported
from plexapi.library import MovieSection, ShowSection
from plexapi.server import PlexServer
from plexapi.video import Movie as PlexMovie, Episode as PlexEpisode

from api.models import Media, Movie, Show, Episode
from common import utils
from . import Adapter


class PlexAdapter(Adapter):
    def __init__(self, plex_account, min_date):
        self.plex_account = plex_account
        self.min_date = min_date
        self.items_limit = 1000

    def fetch(self) -> Optional[List[Media]]:
        plex_server = self.plex_account.server
        if not plex_server:
            return None

        shows_cache = dict()
        result = list()

        plex = PlexServer(plex_server.connection, self.plex_account.token)
        sections = plex.library.sections()
        for section in sections:
            history = section.history(mindate=self.min_date, maxresults=self.items_limit)
            for item in history:
                try:
                    item.reload()
                except Unsupported as e:
                    # logger.warning(f'{item}: {e}')
                    continue

                is_watched = item.isWatched
                if not is_watched:
                    continue

                watched_at = item.lastViewedAt.astimezone(timezone.utc)

                if item.type == PlexMovie.TYPE:
                    movie = Movie(
                        ids=utils.parse_ids(item.guid),
                        title=item.title,
                        year=item.year,
                        watched_at=watched_at,
                    )

                    result.append(movie)
                    continue

                if item.type == PlexEpisode.TYPE:
                    show_key = item.grandparentKey
                    if show_key in shows_cache:
                        show = shows_cache[show_key]
                    else:
                        show_item = plex.library.fetchItem(show_key)

                        show = Show(
                            ids=utils.parse_ids(show_item.guid),
                            title=show_item.title,
                            year=show_item.year,
                        )

                        shows_cache[show_key] = show

                    season = int(item.parentIndex)
                    number = int(item.index)

                    episode = Episode(
                        season=season,
                        number=number,
                        watched_at=watched_at,
                        show=show,
                    )

                    result.append(episode)
                    continue

        return result

    def push(self, items: List[Media]):
        plex_server = self.plex_account.server
        if not plex_server:
            return None

        plex = PlexServer(plex_server.connection, self.plex_account.token)
        sections = plex.library.sections()

        # for item in items:
        #     if isinstance(item, Movie):
        #         for section in sections:
        #             if section.type != MovieSection.TYPE:
        #                 continue
        #
        #             plex_movie = section.get(item.title)
        #             plex_movie.markWatched()
        #
        #     if isinstance(item, Episode):
        #         for section in sections:
        #             if section.type != ShowSection.TYPE:
        #                 continue
        #
        #             plex_show = section.search(item.show.ids)
        #             plex_episode = plex_show.episode(season=item.season, episode=item.number)
        #             plex_episode.markWatched()

        # todo
        return [item.to_dict() for item in items]
