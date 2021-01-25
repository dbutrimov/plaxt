from django.shortcuts import redirect
from django.views.generic import TemplateView

from account.forms import LinkForm
from account.models import TraktAccount
from account.views import ACCOUNT_ID_KEY, build_webhook_uri


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

        return context
