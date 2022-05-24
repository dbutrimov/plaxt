from django.urls import path, re_path

from . import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('delete/', views.DeleteView.as_view(), name='delete'),
    path('link/', views.LinkView.as_view(), name='link'),
    path('link_form/', views.LinkFormView.as_view(), name='link_form'),
    path('servers/', views.ServersView.as_view(), name='servers'),
    path('server_form/', views.ServerFormView.as_view(), name='server_form'),
    path('sync/', views.SyncView.as_view(), name='sync'),
    path('sync_form/', views.SyncFormView.as_view(), name='sync_form'),
    path('confirm/', views.ConfirmView.as_view(), name='confirm'),
    re_path(r'^authorize/?$', views.AuthorizeView.as_view(), name='authorize'),
]
