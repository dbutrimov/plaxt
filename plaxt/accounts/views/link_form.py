from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import render
from django.views import View
from plexapi.myplex import MyPlexAccount

from accounts.forms import LinkForm
from accounts.utils import hx_redirect
from common.models import PlexAccount
from plaxt import settings


class LinkFormView(View):
    http_method_names = ['get', 'post']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return hx_redirect(settings.LOGIN_URL)

        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return render(request, 'link_form.html', {'form': LinkForm()})

    def post(self, request):
        user = request.user

        form = LinkForm(request.POST)
        if not form.is_valid():
            return render(request, 'link_form.html', {'form': form})

        username = form.cleaned_data['username']
        password = form.cleaned_data['password']

        try:
            plex = MyPlexAccount(username, password)
            plex_token = plex.authenticationToken
        except Exception:
            form.add_error(None, ValidationError("Authorization failed!"))
            return render(request, 'link_form.html', {'form': form})

        plex_account = PlexAccount(
            uuid=plex.uuid,
            username=plex.username,
            token=plex_token,
            user=user,
        )

        plex_account.save()

        return HttpResponse(status=204, headers={'HX-Trigger': 'linkChanged'})
