from typing import Optional

from django.contrib.auth.models import User
from django.http import HttpRequest
from django.urls import reverse
from trakt import Trakt
from trakt.core.configuration import OAuthConfiguration
from trakt.objects import Media, Movie, Show, Season, Episode


class MediaType:
    MOVIE = 'movie'
    SHOW = 'show'
    SEASON = 'season'
    EPISODE = 'episode'


def build_trakt_redirect_uri(request: HttpRequest) -> str:
    return request.build_absolute_uri(reverse('authorize'))


def authenticate_trakt(user: User) -> OAuthConfiguration:
    trakt_account = user.traktaccount
    trakt_auth = trakt_account.auth

    return Trakt.configuration.defaults.oauth.from_response(
        response=trakt_auth.to_response(),
        refresh=True,
        username=trakt_account.uuid,
    )


def get_trakt_media_type(media: Media) -> Optional[str]:
    if isinstance(media, Movie):
        return MediaType.MOVIE
    if isinstance(media, Show):
        return MediaType.SHOW
    if isinstance(media, Season):
        return MediaType.SEASON
    if isinstance(media, Episode):
        return MediaType.EPISODE
    return None


def find_trakt_media(ids: dict[str, str], media: str) -> Optional[Media]:
    for service, media_id in ids.items():
        items = Trakt['search'].lookup(media_id, service=service, media=media, per_page=10, exceptions=False)
        if items and len(items) > 0:
            return items[0]

    return None


def find_trakt_media_id(ids: dict[str, str], media: str) -> Optional[str]:
    if not ids:
        return None

    media_id = ids.get('imdb')
    if media_id:
        return media_id

    trakt_media = find_trakt_media(ids, media)
    _, media_id = trakt_media.pk if trakt_media else None
    return media_id
