import json
import logging
from datetime import datetime

from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpRequest, JsonResponse
from django.middleware import csrf
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from plexapi.myplex import MyPlexAccount
from trakt import Trakt

from . import settings, trakt_utils
from .forms import LinkForm
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


def build_trakt_redirect_uri(request: HttpRequest):
    return request.build_absolute_uri(reverse('authorize'))


def build_webhook_uri(request: HttpRequest, account_id):
    return '{0}?id={1}'.format(request.build_absolute_uri('/webhook'), account_id)


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
            with authenticate_trakt(account_id):
                return Trakt['sync/ratings'].add({
                    'movies': movies,
                    'shows': shows,
                })

        return None

    @staticmethod
    def handle_scrobble(metadata, action, progress, account_id):
        movie = trakt_utils.find_movie(metadata)
        if movie:
            with authenticate_trakt(account_id):
                return Trakt['scrobble'].action(
                    action=action,
                    movie=movie,
                    progress=progress,
                )

        episode = trakt_utils.find_episode(metadata)
        if episode:
            with authenticate_trakt(account_id):
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
            'handle_payload: event={0}; type={1}; guid={2}'.format(
                event,
                media_type,
                metadata['guid'],
            ))

        if event == 'media.rate':
            return self.handle_rating(metadata, account_id)

        scrobble_action, scrobble_progress = self.find_scrobble_action(event)
        if scrobble_action:
            return self.handle_scrobble(metadata, scrobble_action, scrobble_progress, account_id)

        return None

    def post(self, request):
        account_id = request.GET['id']
        payload = json.loads(request.POST['payload'])

        account = TraktAccount.objects.get(uuid=account_id)
        plex_account = account.plex_account
        if plex_account:
            account_metadata = payload['Account']
            plex_username = account_metadata['title']
            if plex_account.username.lower() != plex_username.lower():
                return JsonResponse(None)

        result = self.handle_payload(payload, account_id)
        logger.info('result: ' + result)

        return JsonResponse(result)


class AuthorizeView(View):
    http_method_names = ['get']

    def get(self, request):
        auth_code = request.GET['code']
        state = request.GET['state']

        csrf_token = csrf.get_token(request)
        request_csrf_token = csrf._sanitize_token(state)
        if not csrf._compare_masked_tokens(request_csrf_token, csrf_token):
            raise PermissionDenied()

        auth_response = Trakt['oauth'].token_exchange(auth_code, build_trakt_redirect_uri(request))
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

        account = TraktAccount.objects.get(uuid=account_id)

        form = LinkForm(request.POST)
        if not form.is_valid():
            context = {
                'account': account,
                'link_form': form,
                'webhook_uri': build_webhook_uri(request, account.uuid),
            }

            return render(request, 'index.html', context)

        username = form.cleaned_data['username']
        password = form.cleaned_data['password']

        try:
            plex_account = MyPlexAccount(username, password)
            plex_token = plex_account.authenticationToken
        except Exception:
            form.add_error(None, ValidationError("Authorization failed!"))

            context = {
                'account': account,
                'link_form': form,
                'webhook_uri': build_webhook_uri(request, account.uuid),
            }

            return render(request, 'index.html', context)

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
            'redirect_uri': build_trakt_redirect_uri(request),
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

        plex_account = account.plex_account
        link_form = LinkForm() if not plex_account else None

        context.update({
            'account': account,
            'link_form': link_form,
            'webhook_uri': build_webhook_uri(request, account.uuid),
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
