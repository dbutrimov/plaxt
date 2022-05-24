from django.contrib.auth import logout
from django.shortcuts import render
from django.views import View

from accounts.utils import hx_redirect
from plaxt import settings


class DeleteView(View):
    http_method_names = ['get', 'post']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return hx_redirect(settings.LOGIN_URL)

        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return render(request, 'delete_form.html')

    def post(self, request):
        user = request.user

        logout(request)
        user.delete()

        return hx_redirect('index')
