from django.urls import path
from . import views

urlpatterns = [
    path("", views.login_page, name="login_page"),
    path("home/", views.home, name="home"),
    path("logout/", views.spotify_logout, name="spotify_logout"),
    path("spotify/login/", views.spotify_login, name="spotify_login"),
    path("spotify/callback/", views.spotify_callback, name="spotify_callback"),
    path("django-login/", views.django_login, name="django_login"),
]
