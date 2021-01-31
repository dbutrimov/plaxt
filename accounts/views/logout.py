from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views import View


class LogoutView(View):
    http_method_names = ['post']

    def post(self, request):
        logout(request)
        return redirect('index')
