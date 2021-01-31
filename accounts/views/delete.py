from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views import View

from plaxt import settings


class DeleteView(View):
    http_method_names = ['post']

    def post(self, request):
        user = request.user
        if not user.is_authenticated:
            return redirect(f'{settings.LOGIN_URL}?next={request.path}')

        logout(request)
        user.delete()

        return redirect('index')
