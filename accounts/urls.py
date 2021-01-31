from django.urls import path, re_path

from . import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('delete/', views.DeleteView.as_view(), name='delete'),
    path('link/', views.LinkView.as_view(), name='link'),
    path('unlink/', views.UnlinkView.as_view(), name='unlink'),
    re_path(r'^authorize/?$', views.AuthorizeView.as_view(), name='authorize'),
]
