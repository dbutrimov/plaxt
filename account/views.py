import json
import logging
import re
from datetime import datetime

from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest, HttpRequest, JsonResponse
from django.middleware import csrf
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from plexapi.myplex import MyPlexAccount
from trakt import Trakt

from . import settings
from .models import TraktAccount, TraktAuth, PlexAccount

logger = logging.getLogger(__name__)

ACCOUNT_ID_KEY = 'account_id'


def authenticate_trakt(account_id: str):
    account = TraktAccount.objects.get(uuid=account_id)
    auth = account.auth

    return Trakt.configuration.defaults.oauth.from_response(
        response=auth.to_response(),
        refresh=True,
        username=account_id,
    )


def authorize_redirect_uri(request: HttpRequest):
    return request.build_absolute_uri(reverse('authorize'))


def parse_media_id(guid: str):
    match = re.match(r'^.*\.([^.]*)://([^\\?]*).*$', guid, re.IGNORECASE | re.MULTILINE)
    if not match:
        return None

    media_key = match.group(1)
    if media_key.startswith('the'):
        media_key = media_key[3:]

    media_id = match.group(2)

    return media_key, media_id


def find_ids(metadata, key='guid'):
    guid = metadata.get(key)
    if not guid:
        return None

    media_key, media_id = parse_media_id(guid)
    if not media_key or not media_id:
        return None

    return {
        media_key: media_id,
    }


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
        movie = find_movie(metadata)
        movie['rating'] = rating
        movie['rated_at'] = rated_at
        movies.append(movie)

    shows = []
    if media_type == 'show':
        show = find_show(metadata)
        show['rating'] = rating
        show['rated_at'] = rated_at
        shows.append(show)

    if len(movies) > 0 or len(shows) > 0:
        with authenticate_trakt(account_id):
            return Trakt['sync/ratings'].add({
                'movies': movies,
                'shows': shows,
            })

    return None


def handle_scrobble(metadata, action, progress, account_id):
    movie = find_movie(metadata)
    if movie:
        with authenticate_trakt(account_id):
            return Trakt['scrobble'].action(
                action=action,
                movie=movie,
                progress=progress,
            )

    episode = find_episode(metadata)
    if episode:
        with authenticate_trakt(account_id):
            show = find_show(metadata)
            return Trakt['scrobble'].action(
                action=action,
                show=show,
                episode=episode,
                progress=progress,
            )

    return None


def find_scrobble_action(event):
    if event in ['media.play', 'media.resume']:
        return 'start', 0

    if event in ['media.pause']:
        return 'pause', 0

    if event in ['media.stop']:
        return 'stop', 0

    if event in ['media.scrobble']:
        return 'start', 90

    return None


def handle_payload(payload, account_id):
    event = payload['event']
    metadata = payload['Metadata']
    media_type = metadata['type']

    logger.info(
        'handle_payload: event={0}; type={1}; guid={2}'.format(
            event,
            media_type,
            metadata['guid'],
        ))

    if event == 'media.rate':
        return handle_rating(metadata, account_id)

    scrobble_action, scrobble_progress = find_scrobble_action(event)
    if scrobble_action:
        return handle_scrobble(metadata, scrobble_action, scrobble_progress, account_id)

    return None


@method_decorator(csrf_exempt, name='dispatch')
class WebhookView(View):
    http_method_names = ['post']

    def post(self, request):
        account_id = request.GET.get('id')
        if not account_id:
            return HttpResponseBadRequest()

        payload = json.loads(request.POST['payload'])

        account = TraktAccount.objects.get(uuid=account_id)
        plex_account = account.plex_account
        if plex_account:
            account_metadata = payload['Account']
            plex_username = account_metadata['title']
            if plex_account.username.lower() != plex_username.lower():
                return JsonResponse(None)

        result = handle_payload(payload, account_id)
        return JsonResponse(result)


class AuthorizeView(View):
    http_method_names = ['get']

    def get(self, request):
        auth_code = request.GET.get('code')
        state = request.GET.get('state')

        csrf_token = csrf.get_token(request)
        request_csrf_token = csrf._sanitize_token(state)
        if not csrf._compare_masked_tokens(request_csrf_token, csrf_token):
            raise PermissionDenied()

        auth_response = Trakt['oauth'].token_exchange(auth_code, authorize_redirect_uri(request))
        if not auth_response:
            raise Exception()

        with Trakt.configuration.defaults.oauth.from_response(auth_response):
            user_settings = Trakt['users/settings'].get()
            user = user_settings['user']
            user_id = user['ids']['uuid']
            username = user['username']

        account = TraktAccount.objects.filter(uuid=user_id).first()
        if not account:
            account = TraktAccount(
                uuid=user_id,
                username=username,
                auth=TraktAuth(),
            )
        else:
            account.username = username

        auth = account.auth
        if not auth:
            auth = TraktAuth()
            account.auth = auth

        auth.from_response(auth_response)

        auth.save()
        account.save()

        request.session[ACCOUNT_ID_KEY] = account.uuid

        return redirect('index')


class LinkView(View):
    http_method_names = ['post']

    def post(self, request):
        account_id = request.session.get(ACCOUNT_ID_KEY)
        if not account_id:
            return redirect('login')

        username = request.POST.get('username')
        password = request.POST.get('password')

        plex_account = MyPlexAccount(username, password)
        plex_token = plex_account.authenticationToken

        account = TraktAccount.objects.get(uuid=account_id)
        plex = PlexAccount(
            uuid=plex_account.uuid,
            username=plex_account.username,
            token=plex_token,
        )

        plex.save()

        account.plex_account = plex
        account.save()

        return redirect('index')


class UnlinkView(View):
    http_method_names = ['post']

    def post(self, request):
        account_id = request.session.get(ACCOUNT_ID_KEY)
        if not account_id:
            return redirect('login')

        account = TraktAccount.objects.get(uuid=account_id)
        plex_account = account.plex_account
        if plex_account:
            account.plex_account = None
            account.save()

            plex_account.delete()

        return redirect('index')


class LoginView(TemplateView):
    template_name = "login.html"

    def dispatch(self, request, *args, **kwargs):
        account_id = request.session.get(ACCOUNT_ID_KEY)
        if account_id:
            return redirect('index')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        request = self.request

        csrf_token = csrf.get_token(request)
        context.update({
            'action': 'https://trakt.tv/oauth/authorize',
            'client_id': settings.TRAKT_CLIENT,
            'redirect_uri': authorize_redirect_uri(request),
            'response_type': 'code',
            'state': csrf_token,
        })

        return context


class LogoutView(View):
    http_method_names = ['post']

    def post(self, request):
        try:
            del request.session[ACCOUNT_ID_KEY]
        except KeyError:
            pass

        return redirect('index')


class DeleteView(View):
    http_method_names = ['post']

    def post(self, request):
        account_id = request.session.get(ACCOUNT_ID_KEY)
        if not account_id:
            return redirect('login')

        try:
            del request.session[ACCOUNT_ID_KEY]
        except KeyError:
            pass

        account = TraktAccount.objects.get(uuid=account_id)
        account.delete()

        return redirect('index')


class IndexView(TemplateView):
    template_name = "index.html"

    def dispatch(self, request, *args, **kwargs):
        account_id = request.session.get(ACCOUNT_ID_KEY)
        if not account_id:
            return redirect('login')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        request = self.request
        account_id = request.session[ACCOUNT_ID_KEY]
        account = TraktAccount.objects.get(uuid=account_id)

        context.update({
            'account': account,
            'webhook_uri': '{0}?id={1}'.format(request.build_absolute_uri('webhook'), account.uuid),
        })

        # db_plex_account = account.plex_account
        # if db_plex_account:
        #     plex_account = MyPlexAccount(db_plex_account.username, token=db_plex_account.token)
        #     devices = plex_account.devices()
        #     servers = [x for x in devices if x.provides.lower() == 'server']
        #
        #     context.update({
        #         'servers': servers,
        #     })

        return context
