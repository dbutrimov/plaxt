from django.urls import include, path, re_path
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
# router.register(r'webhook', views.WebhookView, basename='Webhook')

urlpatterns = [
    path('', include(router.urls)),
    re_path(r'^webhook/?$', views.WebhookView.as_view(), name='webhook'),
    re_path(r'^servers/?$', views.ServersView.as_view(), name='servers'),
    re_path(r'^sync/?$', views.SyncView.as_view(), name='sync'),
]
