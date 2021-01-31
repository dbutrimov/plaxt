import json
from datetime import datetime

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from trakt import Trakt

from accounts import logger
from common import trakt_utils
from common.models.trakt import TraktAccount


@method_decorator(csrf_exempt, name='dispatch')
class WebhookView(View):
    http_method_names = ['post']

    @staticmethod
    def handle_rating(metadata, account_id):
        media_type = metadata['type']

        rating = metadata['userRating']
        if not rating:
            return None

        rated_at = metadata['lastRatedAt']
        if rated_at:
            rated_at = datetime.fromtimestamp(rated_at).isoformat()

        movies = []
        if media_type == 'movie':
            movie = trakt_utils.find_movie(metadata)
            movie['rating'] = rating
            movie['rated_at'] = rated_at
            movies.append(movie)

        shows = []
        if media_type == 'show':
            show = trakt_utils.find_show(metadata)
            show['rating'] = rating
            show['rated_at'] = rated_at
            shows.append(show)

        if len(movies) > 0 or len(shows) > 0:
            with trakt_utils.authenticate_trakt(account_id):
                return Trakt['sync/ratings'].add({
                    'movies': movies,
                    'shows': shows,
                })

        return None

    @staticmethod
    def handle_scrobble(metadata, action, progress, account_id):
        movie = trakt_utils.find_movie(metadata)
        if movie:
            with trakt_utils.authenticate_trakt(account_id):
                return Trakt['scrobble'].action(
                    action=action,
                    movie=movie,
                    progress=progress,
                )

        episode = trakt_utils.find_episode(metadata)
        if episode:
            with trakt_utils.authenticate_trakt(account_id):
                show = trakt_utils.find_show(metadata)
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

    def handle_payload(self, payload, account_id):
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
            return self.handle_rating(metadata, account_id)

        scrobble_action, scrobble_progress = self.find_scrobble_action(event)
        if scrobble_action:
            return self.handle_scrobble(metadata, scrobble_action, scrobble_progress, account_id)

        return None

    _REJECTED = {'status': 'rejected'}

    def post(self, request):
        account_id = request.GET['id']
        payload = json.loads(request.POST['payload'])

        account = TraktAccount.objects.get(uuid=account_id)
        plex_account = account.plex_account
        if plex_account:
            account_metadata = payload['Account']
            plex_username = account_metadata['title']
            if plex_account.username.lower() != plex_username.lower():
                result = self._REJECTED
                logger.info('result: {0}'.format(result))
                return JsonResponse(result)

        result = self.handle_payload(payload, account_id) or self._REJECTED
        logger.info('result: {0}'.format(result))

        return JsonResponse(result)
