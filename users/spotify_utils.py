import spotipy
from spotipy.oauth2 import SpotifyOAuth
from django.conf import settings

# Required OAuth for Spotify API
def get_spotify_oauth():
    return SpotifyOAuth(
        client_id=settings.SPOTIFY_CLIENT_ID,
        client_secret=settings.SPOTIFY_CLIENT_SECRET,
        redirect_uri=settings.SPOTIFY_REDIRECT_URI,
        scope="user-read-email playlist-modify-public playlist-modify-private"
    )
