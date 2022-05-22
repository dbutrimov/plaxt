import django

import plaxt


def app_info(request):
    return {
        'app_name': 'plaxt',
        'app_version': plaxt.VERSION,
        'app_repo': 'https://github.com/dbutrimov/plaxt',
        'app_developer': 'dbutrimov',
        'app_developer_link': 'https://github.com/dbutrimov',
        'app_license': 'MIT',
        'app_license_link': 'https://github.com/dbutrimov/plaxt/blob/main/LICENSE',
    }


def django_version(request):
    return {
        'django_version': django.get_version(),
    }
