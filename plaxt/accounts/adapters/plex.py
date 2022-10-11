import logging
from datetime import timezone, datetime
from typing import List, Optional, Union, Any

from plexapi.exceptions import Unsupported, NotFound
from plexapi.library import MovieSection, ShowSection, LibrarySection, Library as PlexLibrary
from plexapi.server import PlexServer
from plexapi.video import Movie as PlexMovie, Episode as PlexEpisode, Show as PlexShow

from api.models import Media, Movie, Show, Episode, Season
from common.utils import parse_media_guid
from . import Adapter

logger = logging.getLogger(__name__)


class PlexAdapter(Adapter):
    @staticmethod
    def parse_ids(media: Union[PlexMovie, PlexShow, PlexEpisode]) -> dict[str, str]:
        result = None
        for guid in media.guids:
            service, media_id = parse_media_guid(guid.id)
            if result:
                result.update({service: media_id})
            else:
                result = {service: media_id}

        return result

    @staticmethod
    def find_section_media(item: Union[Movie, Show], section: LibrarySection) -> Optional[Union[PlexMovie, PlexShow]]:
        # find by ids
        if item.ids:
            for key, value in item.ids.items():
                try:
                    result = section.getGuid(f'{key}://{value}')
                    if result:
                        return result
                except NotFound:
                    continue

        # find by title
        try:
            result = section.get(item.title)
            if result:
                return result
        except NotFound:
            pass

        return None

    @staticmethod
    def find_library_media(item: Union[Movie, Show], library: PlexLibrary) -> Optional[Union[PlexMovie, PlexShow]]:
        for section in library.sections():
            if not (section.type == MovieSection.TYPE and item.type == Movie.TYPE) and \
                    not (section.type == ShowSection.TYPE and item.type == Show.TYPE):
                continue

            result = PlexAdapter.find_section_media(item, section)
            if result:
                return result

        return None

    def __init__(self, plex_account):
        self.plex_account = plex_account

    def fetch(self, min_date: datetime = None, items_limit: int = 1000) -> Optional[List[Media]]:
        plex_server = self.plex_account.server
        if not plex_server:
            return None

        result = list()
        shows = dict()

        plex = PlexServer(plex_server.connection, self.plex_account.token)
        history = plex.library.history(mindate=min_date, maxresults=items_limit)
        for plex_item in history:
            try:
                plex_item.reload()
            except Unsupported as e:
                logger.warning(f'{plex_item}: {e}')
                continue

            watched_at = plex_item.lastViewedAt.astimezone(timezone.utc)

            if isinstance(plex_item, PlexMovie):
                movie = Movie(
                    ids=PlexAdapter.parse_ids(plex_item),
                    title=plex_item.originalTitle or plex_item.title,
                    year=plex_item.year,
                    watched_at=watched_at,
                )

                result.append(movie)
                continue

            if isinstance(plex_item, PlexEpisode):
                show_key = plex_item.grandparentKey
                show = shows.get(show_key)
                if not show:
                    plex_show = plex.library.fetchItem(show_key)
                    show = Show(
                        ids=PlexAdapter.parse_ids(plex_show),
                        title=plex_show.originalTitle or plex_show.title,
                        year=plex_show.year,
                    )

                    shows[show_key] = show
                    result.append(show)

                season = next((x for x in show.seasons if x.number == plex_item.seasonNumber), None)
                if not season:
                    season = Season(
                        number=plex_item.seasonNumber,
                    )

                    show.seasons.append(season)

                episode = Episode(
                    ids=PlexAdapter.parse_ids(plex_item),
                    title=plex_item.title or plex_item.seasonEpisode,
                    number=plex_item.episodeNumber,
                    watched_at=watched_at,
                )

                season.episodes.append(episode)
                continue

        return result

    def push(self, items: List[Media]) -> Optional[Any]:
        plex_server = self.plex_account.server
        if not plex_server:
            return {
                'message': 'Plex server is not configured'
            }

        plex = PlexServer(plex_server.connection, self.plex_account.token)
        plex_library = plex.library

        added_movies = 0
        added_episodes = 0
        not_found = list()

        for item in items:
            if isinstance(item, Movie):
                plex_movie = PlexAdapter.find_library_media(item, plex_library)
                if not plex_movie:
                    not_found.append(item.to_dict())
                    continue

                if not plex_movie.isPlayed:
                    plex_movie.markPlayed()
                    added_movies += 1

                continue

            if isinstance(item, Show):
                plex_show = PlexAdapter.find_library_media(item, plex_library)
                if not plex_show:
                    not_found.append(item.to_dict())
                    continue

                not_found_seasons = list()
                for season in item.seasons:
                    not_found_episodes = list()
                    for episode in season.episodes:
                        try:
                            plex_episode = plex_show.episode(season=season.number, episode=episode.number)
                        except NotFound:
                            not_found_episodes.append(episode)
                            continue

                        if not plex_episode.isPlayed:
                            plex_episode.markPlayed()
                            added_episodes += 1

                    if len(not_found_episodes) > 0:
                        not_found_seasons.append(
                            Season(
                                number=season.number,
                                episodes=not_found_episodes,
                            ))

                if len(not_found_seasons) > 0:
                    not_found_show = Show(
                        ids=item.ids,
                        title=item.title,
                        year=item.year,
                        seasons=not_found_seasons,
                    )

                    not_found.append(not_found_show.to_dict())

                continue

            not_found.append(item.to_dict())

        return {
            'added': {
                'movies': added_movies,
                'episodes': added_episodes,
            },
            'not_found': not_found,
        }
