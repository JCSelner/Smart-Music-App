from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path("spotify/login/", views.spotify_login, name="spotify_login"),
    path("spotify/callback/", views.spotify_callback, name="spotify_callback"),
    path("spotify/profile/", views.spotify_profile, name="spotify_profile"),

]