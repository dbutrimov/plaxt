from django.shortcuts import redirect
from django.views.generic import TemplateView

from plaxt import settings


class IndexView(TemplateView):
    template_name = 'index.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)

        return super().dispatch(request, *args, **kwargs)
