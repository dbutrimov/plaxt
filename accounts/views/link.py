from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.views import View
from plexapi.myplex import MyPlexAccount

from accounts.forms import LinkForm
from common import trakt_utils
from common.models.plex import PlexAccount
from plaxt import settings


class LinkView(View):
    http_method_names = ['post']

    def post(self, request):
        user = request.user
        if not user.is_authenticated:
            return redirect(f'{settings.LOGIN_URL}?next={request.path}')

        form = LinkForm(request.POST)
        if not form.is_valid():
            context = {
                'link_form': form,
            }

            return render(request, 'index.html', context)

        username = form.cleaned_data['username']
        password = form.cleaned_data['password']

        try:
            plex = MyPlexAccount(username, password)
            plex_token = plex.authenticationToken
        except Exception:
            form.add_error(None, ValidationError("Authorization failed!"))

            context = {
                'link_form': form,
            }

            return render(request, 'index.html', context)

        plex_account = PlexAccount(
            uuid=plex.uuid,
            username=plex.username,
            token=plex_token,
            user=user,
        )

        plex_account.save()

        return redirect('index')
