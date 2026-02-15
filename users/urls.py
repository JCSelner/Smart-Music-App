from django.urls import path
from . import views

urlpatterns = [
    path("", views.login_page, name="login_page"),  # default root
    path("home/", views.home, name="home"),
    path("spotify/login/", views.spotify_login, name="spotify_login"),
    path("spotify/callback/", views.spotify_callback, name="spotify_callback"),
    path("logout/", views.spotify_logout, name="spotify_logout"),
]
