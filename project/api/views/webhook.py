import json
from datetime import datetime
from typing import Optional, Tuple, Any

from django.contrib.auth.models import User
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request as RestRequest
from rest_framework.response import Response as RestResponse
from rest_framework.views import APIView
from trakt import Trakt
from trakt.objects import Media

from api import logger
from common.models import PlexAccount, TraktAccount
from common.utils import find_trakt_media, find_plex_metadata_ids, get_trakt_media_type, authenticate_trakt, MediaType


def find_trakt_media_by_metadata(metadata: dict) -> Optional[Media]:
    ids = find_plex_metadata_ids(metadata)
    if not ids:
        return None

    media_type = metadata.get('type')
    if not media_type:
        return None

    return find_trakt_media(ids, media_type)


def handle_rating(metadata: dict, user: User) -> Any:
    rating = metadata['userRating']
    if not rating:
        return None

    rated_at = metadata['lastRatedAt']
    if rated_at:
        rated_at = datetime.fromtimestamp(rated_at).isoformat()

    with authenticate_trakt(user):
        trakt_media = find_trakt_media_by_metadata(metadata)
        if not trakt_media:
            return None

        media_type = get_trakt_media_type(trakt_media)
        if not media_type:
            return None

        key = media_type + 's'
        data = {
            'ids': dict(trakt_media.keys),
            'rating': rating,
            'rated_at': rated_at,
        }

        return Trakt['sync/ratings'].add(
            {key: [data]},
            exceptions=True,
        )


def handle_scrobble(metadata: dict, action: str, progress: int, user: User) -> Any:
    with authenticate_trakt(user):
        trakt_media = find_trakt_media_by_metadata(metadata)
        if not trakt_media:
            return None

        data = {
            'ids': dict(trakt_media.keys),
        }

        media_type = get_trakt_media_type(trakt_media)
        if media_type is MediaType.MOVIE:
            return Trakt['scrobble'].action(
                action=action,
                movie=data,
                progress=progress,
                exceptions=True,
            )

        if media_type is MediaType.EPISODE:
            return Trakt['scrobble'].action(
                action=action,
                episode=data,
                progress=progress,
                exceptions=True,
            )

    return None


def find_scrobble_action(event: str) -> Optional[Tuple[str, int]]:
    if event in ['media.play', 'media.resume']:
        return 'start', 0
    if event in ['media.pause']:
        return 'pause', 0
    if event in ['media.stop']:
        return 'stop', 0
    if event in ['media.scrobble']:
        return 'stop', 90
    return None


def handle_payload(payload: dict, user: User) -> Any:
    event = payload['event']
    metadata = payload['Metadata']
    media_type = metadata['type']

    logger.info(
        'handle_payload: {0}'.format({
            'event': event,
            'type': media_type,
            'guid': metadata['guid'],
        }))

    if event is 'media.rate':
        return handle_rating(metadata, user)

    scrobble_action, scrobble_progress = find_scrobble_action(event)
    if scrobble_action:
        return handle_scrobble(metadata, scrobble_action, scrobble_progress, user)

    return None


class WebhookView(APIView):
    parser_classes = [MultiPartParser]
    authentication_classes = []
    permission_classes = []

    def post(self, request: RestRequest):
        uuid = request.GET['id']
        payload = json.loads(request.data['payload'])

        trakt_account = TraktAccount.objects.get(uuid=uuid)
        user = trakt_account.user

        try:
            plex_account = user.plexaccount
        except PlexAccount.DoesNotExist:
            plex_account = None

        if plex_account:
            account_metadata = payload['Account']
            plex_username = account_metadata['title']
            if plex_account.username.lower() != plex_username.lower():
                result = {'status': 'rejected'}
                logger.info('result: {0}'.format(result))
                return RestResponse(result)

        result = handle_payload(payload, user) or {'status': 'rejected'}
        logger.info('result: {0}'.format(result))

        return RestResponse(result)
