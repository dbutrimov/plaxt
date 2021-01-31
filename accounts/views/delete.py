from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views import View

from plaxt import settings


class DeleteView(View):
    http_method_names = ['post']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)

        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        user = request.user

        logout(request)
        user.delete()

        return redirect('index')
