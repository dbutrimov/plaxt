from django.core.exceptions import BadRequest
from django.shortcuts import render
from django.views import View


class ConfirmView(View):
    http_method_names = ['post']

    def post(self, request):
        data = request.POST

        path = data.get('path')
        message = data.get('message')
        if not path or not message:
            return BadRequest()

        context = {
            'method': data.get('method') or 'post',
            'path': path,
            'title': data.get('title') or 'Confirm',
            'message': message,
            'accept': data.get('accept') or 'Yes',
            'decline': data.get('decline') or 'No'
        }

        return render(request, 'confirm.html', context)
