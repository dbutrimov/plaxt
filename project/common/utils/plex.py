from typing import Optional

from django.http import HttpRequest
from .common import parse_media_guid


def build_plex_webhook_uri(request: HttpRequest) -> Optional[str]:
    user = request.user
    if not user or not user.is_authenticated:
        return None

    trakt_account = user.traktaccount
    return '{0}?id={1}'.format(request.build_absolute_uri('/api/webhook'), trakt_account.uuid)


def find_plex_metadata_ids(metadata: dict, key: str = 'Guid') -> Optional[dict[str, str]]:
    guids = metadata.get(key)
    if not guids:
        return None

    result = dict()
    for item in guids:
        guid = item.get('id')
        if not guid:
            continue

        service, media_id = parse_media_guid(guid)
        if not service or not media_id:
            continue

        result[service] = media_id

    return result
