from django import template

from common import trakt_utils

register = template.Library()


@register.filter
def webhook_uri(request):
    return trakt_utils.build_webhook_uri(request)
