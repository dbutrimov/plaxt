from django.urls import include, path, re_path
from rest_framework import routers

# from api.views.webhook import WebhookView

router = routers.DefaultRouter()
# router.register(r'webhook', WebhookView, basename='Webhook')

urlpatterns = [
    path('', include(router.urls)),
    # re_path(r'^webhook/?$', WebhookView.as_view()),
]
