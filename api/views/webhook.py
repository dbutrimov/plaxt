import json
from datetime import datetime

from rest_framework.exceptions import ParseError
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request as RestRequest
from rest_framework.response import Response as RestResponse
from rest_framework.views import APIView
from trakt import Trakt

from api import logger
from common import utils
from common.models import PlexAccount, TraktAccount


class WebhookView(APIView):
    @staticmethod
    def handle_rating(metadata, user):
        media_type = metadata['type']

        rating = metadata['userRating']
        if not rating:
            return None

        rated_at = metadata['lastRatedAt']
        if rated_at:
            rated_at = datetime.fromtimestamp(rated_at).isoformat()

        movies = []
        if media_type == 'movie':
            movie = utils.find_movie(metadata)
            movie['rating'] = rating
            movie['rated_at'] = rated_at
            movies.append(movie)

        shows = []
        if media_type == 'show':
            show = utils.find_show(metadata)
            show['rating'] = rating
            show['rated_at'] = rated_at
            shows.append(show)

        if len(movies) > 0 or len(shows) > 0:
            with utils.authenticate_trakt(user):
                return Trakt['sync/ratings'].add({
                    'movies': movies,
                    'shows': shows,
                })

        return None

    @staticmethod
    def handle_scrobble(metadata, action, progress, user):
        movie = utils.find_movie(metadata)
        if movie:
            with utils.authenticate_trakt(user):
                return Trakt['scrobble'].action(
                    action=action,
                    movie=movie,
                    progress=progress,
                )

        episode = utils.find_episode(metadata)
        if episode:
            with utils.authenticate_trakt(user):
                show = utils.find_show(metadata)
                return Trakt['scrobble'].action(
                    action=action,
                    show=show,
                    episode=episode,
                    progress=progress,
                )

        return None

    @staticmethod
    def find_scrobble_action(event):
        if event in ['media.play', 'media.resume']:
            return 'start', 0

        if event in ['media.pause']:
            return 'pause', 0

        if event in ['media.stop']:
            return 'stop', 0

        if event in ['media.scrobble']:
            return 'stop', 90

        return None

    def handle_payload(self, payload, user):
        event = payload['event']
        metadata = payload['Metadata']
        media_type = metadata['type']

        logger.info(
            'handle_payload: {0}'.format({
                'event': event,
                'type': media_type,
                'guid': metadata['guid'],
            }))

        if event == 'media.rate':
            return self.handle_rating(metadata, user)

        scrobble_action, scrobble_progress = self.find_scrobble_action(event)
        if scrobble_action:
            return self.handle_scrobble(metadata, scrobble_action, scrobble_progress, user)

        return None

    parser_classes = [MultiPartParser]
    authentication_classes = []
    permission_classes = []

    def post(self, request: RestRequest):
        uuid = request.GET['id']
        payload = json.loads(request.data['payload'])

        try:
            trakt_account = TraktAccount.objects.get(uuid=uuid)
        except TraktAccount.DoesNotExist:
            raise ParseError()

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

        result = self.handle_payload(payload, user) or {'status': 'rejected'}
        logger.info('result: {0}'.format(result))

        return RestResponse(result)
