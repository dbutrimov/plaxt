from django.urls import include, path, re_path
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
# router.register(r'tasks', views.TasksView, basename='task')

urlpatterns = [
    path('', include(router.urls)),
    re_path(r'^webhook/?$', views.WebhookView.as_view(), name='webhook'),
    re_path(r'^servers/?$', views.ServersView.as_view(), name='servers'),
    re_path(r'^sync/?$', views.SyncView.as_view(), name='sync'),
    re_path(r'^sync/state/?$', views.SyncStateView.as_view(), name='sync_state'),
    # re_path(r'^tasks/?$', views.TasksView.as_view(), name='tasks'),
]
