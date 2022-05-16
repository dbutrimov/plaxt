from django.urls import include, path, re_path
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
# router.register(r'tasks', views.TasksView, basename='task')

urlpatterns = [
    path('', include(router.urls)),
    re_path(r'^webhook/?$', views.WebhookView.as_view(), name='webhook'),
]
