from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.views import View
from plexapi.myplex import MyPlexAccount

from account.forms import LinkForm
from account.models import TraktAccount, PlexAccount
from account.views import ACCOUNT_ID_KEY, build_webhook_uri


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
