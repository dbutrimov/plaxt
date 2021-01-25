from django.urls import path, re_path

from account.views.authorize import AuthorizeView
from account.views.delete import DeleteView
from account.views.index import IndexView
from account.views.link import LinkView
from account.views.login import LoginView
from account.views.logout import LogoutView
from account.views.servers import ServersView
from account.views.sync import SyncView
from account.views.unlink import UnlinkView
from account.views.webhook import WebhookView

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
