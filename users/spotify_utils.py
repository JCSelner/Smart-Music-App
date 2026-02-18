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

def create_playlist_for_user(request, name, description, track_uris):
    sp = spotipy.Spotify(auth=request.session.get("spotify_access_token"))

    # Get current Spotify user
    user_profile = sp.current_user()
    user_id = user_profile["id"]

    # Create playlist
    playlist = sp.user_playlist_create(
        user=user_id,
        name=name,
        public=False,
        description=description
    )

    # Add tracks
    sp.playlist_add_items(
        playlist_id=playlist["id"],
        items=track_uris
    )

    return playlist
