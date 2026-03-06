from django.test import TestCase, RequestFactory
from unittest.mock import patch, MagicMock, call
from django.contrib.auth import get_user_model

User = get_user_model()


class GetSpotifyOAuthTests(TestCase):

    @patch("users.spotify_utils.SpotifyOAuth")
    def test_get_spotify_oauth_returns_oauth_object(self, mock_oauth_class):
        from users.spotify_utils import get_spotify_oauth

        mock_oauth_instance = MagicMock()
        mock_oauth_class.return_value = mock_oauth_instance

        result = get_spotify_oauth()

        self.assertEqual(result, mock_oauth_instance)
        mock_oauth_class.assert_called_once()

    @patch("users.spotify_utils.SpotifyOAuth")
    def test_get_spotify_oauth_uses_correct_scope(self, mock_oauth_class):
        from users.spotify_utils import get_spotify_oauth

        get_spotify_oauth()

        _, kwargs = mock_oauth_class.call_args
        scope = kwargs.get("scope", "")
        self.assertIn("user-read-email", scope)
        self.assertIn("playlist-modify-public", scope)
        self.assertIn("playlist-modify-private", scope)

    @patch("users.spotify_utils.SpotifyOAuth")
    def test_get_spotify_oauth_passes_settings_credentials(self, mock_oauth_class):
        from users.spotify_utils import get_spotify_oauth
        from django.conf import settings

        get_spotify_oauth()

        _, kwargs = mock_oauth_class.call_args
        self.assertEqual(kwargs.get("client_id"), settings.SPOTIFY_CLIENT_ID)
        self.assertEqual(kwargs.get("client_secret"), settings.SPOTIFY_CLIENT_SECRET)
        self.assertEqual(kwargs.get("redirect_uri"), settings.SPOTIFY_REDIRECT_URI)


class CreatePlaylistForUserTests(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="playlist_user", password="pass123")

    def _make_request(self, access_token="test_access_token"):
        request = self.factory.get("/")
        request.session = {"spotify_access_token": access_token}
        return request

    @patch("users.spotify_utils.spotipy.Spotify")
    def test_create_playlist_calls_user_playlist_create(self, mock_spotify_class):
        from users.spotify_utils import create_playlist_for_user

        mock_sp = MagicMock()
        mock_sp.current_user.return_value = {"id": "spotify_user_123"}
        mock_sp.user_playlist_create.return_value = {
            "id": "playlist_id_abc",
            "external_urls": {"spotify": "https://open.spotify.com/playlist/abc"},
        }
        mock_spotify_class.return_value = mock_sp

        request = self._make_request()
        track_uris = ["spotify:track:1", "spotify:track:2"]

        result = create_playlist_for_user(request, "My Playlist", "A great playlist", track_uris)

        mock_sp.user_playlist_create.assert_called_once_with(
            user="spotify_user_123",
            name="My Playlist",
            public=False,
            description="A great playlist",
        )

    @patch("users.spotify_utils.spotipy.Spotify")
    def test_create_playlist_adds_tracks(self, mock_spotify_class):
        from users.spotify_utils import create_playlist_for_user

        mock_sp = MagicMock()
        mock_sp.current_user.return_value = {"id": "spotify_user_123"}
        mock_sp.user_playlist_create.return_value = {
            "id": "playlist_id_abc",
            "external_urls": {"spotify": "https://open.spotify.com/playlist/abc"},
        }
        mock_spotify_class.return_value = mock_sp

        request = self._make_request()
        track_uris = ["spotify:track:1", "spotify:track:2"]

        create_playlist_for_user(request, "My Playlist", "desc", track_uris)

        mock_sp.playlist_add_items.assert_called_once_with(
            playlist_id="playlist_id_abc",
            items=track_uris,
        )

    @patch("users.spotify_utils.spotipy.Spotify")
    def test_create_playlist_returns_playlist_object(self, mock_spotify_class):
        from users.spotify_utils import create_playlist_for_user

        mock_sp = MagicMock()
        mock_sp.current_user.return_value = {"id": "spotify_user_123"}
        expected_playlist = {
            "id": "playlist_id_abc",
            "external_urls": {"spotify": "https://open.spotify.com/playlist/abc"},
        }
        mock_sp.user_playlist_create.return_value = expected_playlist
        mock_spotify_class.return_value = mock_sp

        request = self._make_request()
        result = create_playlist_for_user(request, "My Playlist", "desc", [])

        self.assertEqual(result, expected_playlist)

    @patch("users.spotify_utils.spotipy.Spotify")
    def test_create_playlist_uses_session_access_token(self, mock_spotify_class):
        from users.spotify_utils import create_playlist_for_user

        mock_sp = MagicMock()
        mock_sp.current_user.return_value = {"id": "user_x"}
        mock_sp.user_playlist_create.return_value = {"id": "pid", "external_urls": {}}
        mock_spotify_class.return_value = mock_sp

        request = self._make_request(access_token="my_special_token")
        create_playlist_for_user(request, "Test", "desc", [])

        mock_spotify_class.assert_called_once_with(auth="my_special_token")

    @patch("users.spotify_utils.spotipy.Spotify")
    def test_create_playlist_with_empty_track_list(self, mock_spotify_class):
        from users.spotify_utils import create_playlist_for_user

        mock_sp = MagicMock()
        mock_sp.current_user.return_value = {"id": "user_x"}
        mock_sp.user_playlist_create.return_value = {"id": "pid", "external_urls": {}}
        mock_spotify_class.return_value = mock_sp

        request = self._make_request()
        # Should not raise even with an empty track list
        create_playlist_for_user(request, "Empty Playlist", "no tracks", [])
        mock_sp.playlist_add_items.assert_called_once_with(playlist_id="pid", items=[])