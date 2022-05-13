from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.views import View
from plexapi.myplex import MyPlexAccount

from accounts.forms import LinkForm
from common.models import PlexAccount
from plaxt import settings


class LinkView(View):
    http_method_names = ['post']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)

        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        user = request.user

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
