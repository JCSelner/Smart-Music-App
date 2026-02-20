from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

from users.models import SpotifyToken

User = get_user_model()


class LoginTests(TestCase):

    def setUp(self):
        # Create a regular Django user
        self.user = User.objects.create_user(
            username="testuser",
            password="TestPass123",
            email="test@example.com"
        )

        # If your custom user has role field
        if hasattr(self.user, "role"):
            self.user.role = "user"
            self.user.save()

    # -------------------------
    # Django login tests
    # -------------------------

    def test_django_login_success(self):
        response = self.client.post(
            reverse("django_login"),
            {"username": "testuser", "password": "TestPass123"}
        )
        self.assertRedirects(response, reverse("dashboard"))

    def test_django_login_failure(self):
        response = self.client.post(
            reverse("django_login"),
            {"username": "testuser", "password": "WrongPass"}
        )
        self.assertRedirects(response, reverse("login_page"))

    # -------------------------
    # Spotify login tests
    # -------------------------

    @patch("users.views.get_spotify_oauth")
    def test_spotify_login_redirect(self, mock_oauth):
        mock_instance = MagicMock()
        mock_instance.get_authorize_url.return_value = "https://spotify.com/auth"
        mock_oauth.return_value = mock_instance

        response = self.client.get(reverse("spotify_login"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "https://spotify.com/auth")

    @patch("users.views.spotipy.Spotify")
    @patch("users.views.get_spotify_oauth")
    def test_spotify_callback_creates_user(
        self, mock_oauth, mock_spotify
    ):
        # Mock token response
        mock_oauth_instance = MagicMock()
        mock_oauth_instance.get_access_token.return_value = {
            "access_token": "ACCESS123",
            "refresh_token": "REFRESH123",
            "expires_at": 9999999999
        }
        mock_oauth.return_value = mock_oauth_instance

        # Mock Spotify user
        mock_spotify_instance = MagicMock()
        mock_spotify_instance.current_user.return_value = {
            "id": "spotifyuser",
            "display_name": "Spotify User",
            "email": "spotify@example.com"
        }
        mock_spotify.return_value = mock_spotify_instance

        response = self.client.get(
            reverse("spotify_callback"),
            {"code": "fakecode"}
        )

        self.assertRedirects(response, reverse("dashboard"))

        # Confirm user created
        user = User.objects.get(username="spotifyuser")
        self.assertEqual(user.email, "spotify@example.com")

        # Confirm token saved
        token = SpotifyToken.objects.get(user=user)
        self.assertEqual(token.access_token, "ACCESS123")
