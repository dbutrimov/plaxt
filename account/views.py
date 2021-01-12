import json
import re

from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest, HttpRequest
from django.middleware import csrf
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.exceptions import ParseError
from rest_framework.request import Request as RestRequest
from rest_framework.response import Response as RestResponse
from trakt import Trakt

from . import settings
from .models import TraktAccount, TraktAuth

ACCOUNT_ID_KEY = 'account_id'


def authenticate_trakt(account_id: str):
    account = TraktAccount.objects.get(id=account_id)
    auth = account.auth

    return Trakt.configuration.defaults.oauth.from_response(
        response=auth.to_response(),
        refresh=True,
        username=account.username,
    )


def authorize_redirect_uri(request: HttpRequest):
    return request.build_absolute_uri(reverse('authorize'))


# media.pause – Media playback pauses.
# media.play – Media starts playing. An appropriate poster is attached.
# media.rate – Media is rated. A poster is also attached to this event.
# media.resume – Media playback resumes.
# media.scrobble – Media is viewed (played past the 90% mark).
# media.stop – Media playback stops.
def get_action(event):
    if event in ['media.play', 'media.resume']:
        return 'start', 0

    if event in ['media.pause']:
        return 'pause', 0

    if event in ['media.stop']:
        return 'stop', 0

    if event in ['media.scrobble']:
        return 'stop', 90

    return None


def parse_media_id(guid: str):
    match = re.match(r'^.*\.([^.]*)://([^\\?]*).*$', guid, re.IGNORECASE | re.MULTILINE)
    if not match:
        return None

    media_key = match.group(1)
    if media_key.startswith('the'):
        media_key = media_key[3:]

    media_id = match.group(2)

    return media_key, media_id


def handle_movie(metadata, event, account_id):
    # {
    #     'librarySectionType': 'movie',
    #     'ratingKey': '10227',
    #     'key': '/library/metadata/10227',
    #     'guid': 'com.plexapp.agents.imdb://tt9204164?lang=ru',
    #     'studio': 'nWave Pictures',
    #     'type': 'movie',
    #     'title': 'Семейка Бигфутов',
    #     'librarySectionTitle': 'Movies',
    #     'librarySectionID': 1,
    #     'librarySectionKey': '/library/sections/1',
    #     'originalTitle': 'Bigfoot Family',
    #     'summary': 'Все семьи разные, но эта — самая разношерстная. Папа когда-то превратился в Бигфута, сын унаследовал его суперспособности и умение понимать язык животных, так ещё и в доме вместе с ними и мамой живёт целый зоопарк — огромный медведь, неутомимая белка и беспокойный енот со множеством очаровательных детёнышей. Когда же уникальному заповеднику на Аляске понадобится помощь, вся семейка Бигфутов отправится в большое путешествие и покажет всему миру, на что способна их команда…',
    #     'rating': 5.5,
    #     'viewCount': 3,
    #     'lastViewedAt': 1610277754,
    #     'year': 2020,
    #     'tagline': 'Все семьи как семьи... Но эта - самая разношёрстная',
    #     'thumb': '/library/metadata/10227/thumb/1609715876',
    #     'art': '/library/metadata/10227/art/1609715876',
    #     'duration': 5820000,
    #     'originallyAvailableAt': '2020-07-23',
    #     'addedAt': 1604909771,
    #     'updatedAt': 1609715876,
    #     'chapterSource': 'media'
    # }

    action, progress = get_action(event)
    if not action:
        raise ParseError()

    with authenticate_trakt(account_id):
        ids = dict()
        guid = metadata['guid']
        media_key, media_id = parse_media_id(guid)
        if media_id:
            ids[media_key] = media_id

        movie = {
            'title': metadata['originalTitle'],
            'year': metadata['year'],
            'ids': ids,
        }

        result = Trakt['scrobble'].action(
            action=action,
            movie=movie,
            progress=progress,
        )

    return result


def handle_show(metadata, event, account_id):
    # {
    #     'librarySectionType': 'show',
    #     'ratingKey': '10358',
    #     'key': '/library/metadata/10358',
    #     'parentRatingKey': '10357',
    #     'grandparentRatingKey': '2759',
    #     'guid': 'com.plexapp.agents.thetvdb://350665/3/1?lang=ru',
    #     'parentGuid': 'com.plexapp.agents.thetvdb://350665/3?lang=ru',
    #     'grandparentGuid': 'com.plexapp.agents.thetvdb://350665?lang=ru',
    #     'type': 'episode',
    #     'title': 'Последствия',
    #     'grandparentKey': '/library/metadata/2759',
    #     'parentKey': '/library/metadata/10357',
    #     'librarySectionTitle': 'TV Shows',
    #     'librarySectionID': 2,
    #     'librarySectionKey': '/library/sections/2',
    #     'grandparentTitle': 'Новобранец',
    #     'parentTitle': 'Season 3',
    #     'contentRating': 'TV-14',
    #     'summary': '',
    #     'index': 1,
    #     'parentIndex': 3,
    #     'viewOffset': 80000,
    #     'viewCount': 1,
    #     'lastViewedAt': 1610366060,
    #     'year': 2021,
    #     'thumb': '/library/metadata/10358/thumb/1609872030',
    #     'art': '/library/metadata/2759/art/1609872030',
    #     'parentThumb': '/library/metadata/10357/thumb/1609872030',
    #     'grandparentThumb': '/library/metadata/2759/thumb/1609872030',
    #     'grandparentArt': '/library/metadata/2759/art/1609872030',
    #     'grandparentTheme': '/library/metadata/2759/theme/1609872030',
    #     'originallyAvailableAt': '2021-01-01',
    #     'addedAt': 1609872000,
    #     'updatedAt': 1609872030
    # }

    action, progress = get_action(event)
    if not action:
        raise ParseError()

    with authenticate_trakt(account_id):
        ids = dict()
        guid = metadata['grandparentGuid']
        media_key, media_id = parse_media_id(guid)
        if media_id:
            ids[media_key] = media_id

        show = {
            'title': metadata['title'],
            'year': metadata['year'],
            'ids': ids,
        }

        episode = {
            'season': metadata['parentIndex'],
            'number': metadata['index']
        }

        result = Trakt['scrobble'].action(
            action=action,
            show=show,
            episode=episode,
            progress=progress,
        )

    return result


@csrf_exempt
@api_view(['POST'])
# @parser_classes([JSONParser])
def webhook(request: RestRequest, format=None):
    account_id = request.query_params.get('id')
    if not account_id:
        return HttpResponseBadRequest()

    payload = json.loads(request.data['payload'])

    # plex_account = payload['Account']
    metadata = payload['Metadata']

    library_section_type = metadata['librarySectionType']
    if library_section_type == 'movie':
        result = handle_movie(metadata, payload['event'], account_id)
        return RestResponse(result)

    if library_section_type == 'show':
        result = handle_show(metadata, payload['event'], account_id)
        return RestResponse(result)

    return RestResponse({'success': True})


def authorize(request: HttpRequest):
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

    account = TraktAccount.objects.filter(username=username).first()
    if not account:
        account = TraktAccount(
            id=user_id,
            username=username,
            auth=TraktAuth(),
        )

    auth = account.auth
    if not auth:
        auth = TraktAuth()
        account.auth = auth

    auth.from_response(auth_response)

    auth.save()
    account.save()

    request.session[ACCOUNT_ID_KEY] = account.id

    return redirect('index')


def login(request: HttpRequest):
    if ACCOUNT_ID_KEY in request.session:
        return redirect('index')

    # url = '{0}?client_id={1}&redirect_uri={2}&response_type={3}'.format(
    #     'https://trakt.tv/oauth/authorize',
    #     settings.TRAKT_CLIENT,
    #     urllib.parse.quote(redirect_uri(request), safe=''),
    #     'code',
    # )
    #
    # return redirect(url)

    csrf_token = csrf.get_token(request)
    context = {
        'action': 'https://trakt.tv/oauth/authorize',
        'client_id': settings.TRAKT_CLIENT,
        'redirect_uri': authorize_redirect_uri(request),
        'response_type': 'code',
        'state': csrf_token,
    }

    return render(request, 'login.html', context)


def logout(request: HttpRequest):
    try:
        del request.session[ACCOUNT_ID_KEY]
    except KeyError:
        pass
    return redirect('index')


def delete(request: HttpRequest):
    account_id = request.session.get(ACCOUNT_ID_KEY)
    if not account_id:
        return redirect('login')

    try:
        del request.session[ACCOUNT_ID_KEY]
    except KeyError:
        pass

    account = TraktAccount.objects.get(id=account_id)
    account.delete()

    return redirect('index')


def index(request: HttpRequest):
    if ACCOUNT_ID_KEY not in request.session:
        return redirect('login')

    account_id = request.session.get(ACCOUNT_ID_KEY)
    if not account_id:
        return render(request, 'index.html', {})

    account = TraktAccount.objects.get(id=account_id)

    context = {
        'account': account,
        'webhook_uri': '{0}?id={1}'.format(request.build_absolute_uri('webhook'), account.id),
    }

    return render(request, 'index.html', context)
