from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import TraktAccount


class TraktAccountAdmin(admin.ModelAdmin):
    title = _('Trakt Account')
    list_display = ('id', 'username', 'created_at',)


admin.site.register(TraktAccount, TraktAccountAdmin)
