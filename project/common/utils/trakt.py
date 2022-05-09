import re
from typing import Optional

from django.contrib.auth.models import User
from django.http import HttpRequest
from django.urls import reverse
from trakt import Trakt


def authenticate_trakt(user: User):
    trakt_account = user.traktaccount
    trakt_auth = trakt_account.auth

    return Trakt.configuration.defaults.oauth.from_response(
        response=trakt_auth.to_response(),
        refresh=True,
        username=trakt_account.uuid,
    )


def build_trakt_redirect_uri(request: HttpRequest):
    return request.build_absolute_uri(reverse('authorize'))


def build_webhook_uri(request: HttpRequest):
    user = request.user
    if not user or not user.is_authenticated:
        return None

    trakt_account = user.traktaccount
    return '{0}?id={1}'.format(request.build_absolute_uri('/api/webhook'), trakt_account.uuid)


def parse_media_id(guid: str) -> Optional[tuple[str, str]]:
    match = re.match(r'^(?:[^.]+\.)?([^.]*)://([^\\?]*).*$', guid, re.IGNORECASE | re.MULTILINE)
    if not match:
        return None

    media_key = match.group(1)
    media_id = match.group(2)
    return media_key, media_id


def parse_ids(guid: str) -> Optional[dict[str, str]]:
    media_key, media_id = parse_media_id(guid)
    if not media_key or not media_id:
        return None

    result = {
        media_key: media_id,
    }

    return result


def find_ids(metadata, key='guid') -> Optional[dict[str, str]]:
    guid = metadata.get(key)
    if not guid:
        return None

    return parse_ids(guid)


def find_movie(metadata):
    media_type = metadata.get('type')
    if media_type != 'movie':
        return None

    return {
        'title': metadata['title'],
        'year': metadata['year'],
        'ids': find_ids(metadata),
    }


def find_show(metadata):
    media_type = metadata.get('type')

    if media_type == 'show':
        return {
            'title': metadata['title'],
            'year': metadata['year'],
            'ids': find_ids(metadata),
        }

    if media_type == 'season':
        return {
            'title': metadata['parentTitle'],
            'ids': find_ids(metadata, key='parentGuid'),
        }

    if media_type == 'episode':
        return {
            'title': metadata['grandparentTitle'],
            'ids': find_ids(metadata, key='grandparentGuid'),
        }

    return None


def find_season(metadata):
    media_type = metadata.get('type')

    if media_type == 'season':
        return {
            'title': metadata['title'],
            'season': metadata['index'],
            'ids': find_ids(metadata),
        }

    if media_type == 'episode':
        return {
            'title': metadata['parentTitle'],
            'season': metadata['parentIndex'],
            'ids': find_ids(metadata, key='parentGuid'),
        }

    return None


def find_episode(metadata):
    media_type = metadata.get('type')
    if media_type != 'episode':
        return None

    return {
        'season': metadata['parentIndex'],
        'number': metadata['index'],
        'title': metadata['title'],
        'year': metadata['year'],
        'ids': find_ids(metadata),
    }
