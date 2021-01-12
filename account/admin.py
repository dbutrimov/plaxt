from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import TraktAuth, TraktAccount


class TraktAuthAdmin(admin.ModelAdmin):
    title = _('Trakt Auth')


class TraktAccountAdmin(admin.ModelAdmin):
    title = _('Trakt Account')
    list_display = ('id', 'username', 'created_at',)


admin.site.register(TraktAuth, TraktAuthAdmin)
admin.site.register(TraktAccount, TraktAccountAdmin)
