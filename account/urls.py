from django.urls import path, re_path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login, name='login'),
    path('link/', views.link, name='link'),
    path('unlink/', views.unlink, name='unlink'),
    path('logout/', views.logout, name='logout'),
    path('delete/', views.delete, name='delete'),
    re_path(r'^authorize/?$', views.authorize, name='authorize'),
    re_path(r'^webhook/?$', views.webhook, name='webhook'),
]
