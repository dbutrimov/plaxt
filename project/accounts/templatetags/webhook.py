from django import template

from common import utils

register = template.Library()


@register.filter
def webhook_uri(request):
    return utils.build_webhook_uri(request)
