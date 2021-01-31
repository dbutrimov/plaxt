from django.contrib.auth import authenticate, login
from django.core.exceptions import PermissionDenied
from django.middleware import csrf
from django.shortcuts import redirect
from django.views import View


class AuthorizeView(View):
    http_method_names = ['get']

    def get(self, request):
        auth_code = request.GET['code']
        state = request.GET['state']

        csrf_token = csrf.get_token(request)
        request_csrf_token = csrf._sanitize_token(state)
        if not csrf._compare_masked_tokens(request_csrf_token, csrf_token):
            raise PermissionDenied()

        user = authenticate(request, auth_code=auth_code)
        login(request, user)

        return redirect('index')
