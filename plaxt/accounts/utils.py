from django.shortcuts import redirect


def hx_redirect(to, *args, permanent=False, **kwargs):
    result = redirect(to, *args, permanent, **kwargs)
    result['HX-Redirect'] = result['Location']
    return result
