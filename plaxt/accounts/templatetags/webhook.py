from django import template

from common.utils import build_plex_webhook_uri

register = template.Library()


@register.filter
def webhook_uri(request):
    return build_plex_webhook_uri(request)
