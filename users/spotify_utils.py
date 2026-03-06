import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyOauthError
from django.conf import settings

def get_valid_spotify_client(user):
    """Returns a spotipy client with a valid (refreshed if needed) token for the given user."""
    from .models import SpotifyToken
    token_obj = SpotifyToken.objects.get(user=user)

    if int(time.time()) >= token_obj.expires_at:
        try:
            sp_oauth = get_spotify_oauth()
            token_info = sp_oauth.refresh_access_token(token_obj.refresh_token)
            token_obj.access_token = token_info["access_token"]
            token_obj.expires_at = token_info["expires_at"]
            token_obj.save()
        except SpotifyOauthError:
            token_obj.delete()
            raise SpotifyToken.DoesNotExist

    return spotipy.Spotify(auth=token_obj.access_token)

# Required OAuth for Spotify API
def get_spotify_oauth():
    return SpotifyOAuth(
        client_id=settings.SPOTIFY_CLIENT_ID,
        client_secret=settings.SPOTIFY_CLIENT_SECRET,
        redirect_uri=settings.SPOTIFY_REDIRECT_URI,
        scope="user-read-email user-top-read playlist-modify-public playlist-modify-private"
    )