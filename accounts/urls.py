from django.urls import path, re_path

from accounts.views.authorize import AuthorizeView
from accounts.views.delete import DeleteView
from accounts.views.index import IndexView
from accounts.views.link import LinkView
from accounts.views.login import LoginView
from accounts.views.logout import LogoutView
from accounts.views.servers import ServersView
from accounts.views.sync import SyncView
from accounts.views.unlink import UnlinkView
from accounts.views.webhook import WebhookView

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('delete/', DeleteView.as_view(), name='delete'),
    path('link/', LinkView.as_view(), name='link'),
    path('unlink/', UnlinkView.as_view(), name='unlink'),
    re_path(r'^servers/?$', ServersView.as_view(), name='servers'),
    re_path(r'^authorize/?$', AuthorizeView.as_view(), name='authorize'),
    re_path(r'^webhook/?$', WebhookView.as_view(), name='webhook'),
    re_path(r'^sync/?$', SyncView.as_view(), name='sync'),
]
