from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("", views.login_page, name="login_page"),
    path("dashboard/", views.dashboard, name = "dashboard"),
    path("generate/", views.generate_page, name="generate"),        # add when ready
    path("playlists/", views.playlists_page, name="playlists"),     # add when ready
    path("preferences/", views.preferences_page, name="preferences"), # add when ready
    path("profile/", views.profile_page, name="profile"), #add when ready
    path("logout/", views.spotify_logout, name="spotify_logout"),
    path("spotify/login/", views.spotify_login, name="spotify_login"),
    path("spotify/callback/", views.spotify_callback, name="spotify_callback"),
    path("django-login/", views.django_login, name="django_login"),
    path("generate-playlist/", views.generate_playlist, name="generate_playlist"),
    path("signup/", views.signup_page, name="signup_page"),
    path("password-change/", views.password_change, name="password_change"),
    path("api/weather/", views.get_weather, name="get_weather"),
]
