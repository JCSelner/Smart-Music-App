from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from users.models import SpotifyToken

User = get_user_model()


class ViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="test1234",
            email="test@example.com",
        )
        if hasattr(self.user, "role"):
            self.user.role = "user"
            self.user.save()

    # -------------------------
    # login_page view
    # -------------------------
    def test_login_page_renders_when_not_authenticated(self):
        response = self.client.get(reverse("login_page"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "login.html")

    def test_login_page_redirects_when_authenticated(self):
        self.client.login(username="testuser", password="test1234")
        response = self.client.get(reverse("login_page"))
        self.assertRedirects(response, reverse("dashboard"))

    # -------------------------
    # dashboard view
    # -------------------------
    @patch("users.views.spotipy.Spotify")
    def test_dashboard_with_spotify_token(self, mock_spotify):
        self.client.login(username="testuser", password="test1234")

        SpotifyToken.objects.create(
            user=self.user,
            access_token="ACCESS123",
            refresh_token="REFRESH123",
            expires_at=9999999999,
        )

        mock_spotify_instance = MagicMock()
        mock_spotify_instance.current_user.return_value = {"display_name": "Spotify Name"}
        mock_spotify.return_value = mock_spotify_instance

        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard.html")
        self.assertTrue(response.context["spotify_linked"])
        self.assertEqual(response.context["display_name"], "Spotify Name")
        self.assertIn("time_of_day", response.context)

    def test_dashboard_without_spotify_token(self):
        self.client.login(username="testuser", password="test1234")

        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard.html")
        self.assertFalse(response.context["spotify_linked"])
        self.assertEqual(response.context["display_name"], "testuser")
        self.assertIn("time_of_day", response.context)

    # -------------------------
    # get_weather view
    # -------------------------
    @patch("users.views.get_weather_data")
    def test_get_weather_with_city_success(self, mock_get_weather):
        self.client.login(username="testuser", password="test1234")

        mock_get_weather.return_value = {
            "city": "Milwaukee ",
            "temperature": 32,
            "conditions": "clear sky",
        }

        response = self.client.get(reverse("get_weather"), {"city": "Milwaukee "})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["city"], "Milwaukee ")
        mock_get_weather.assert_called_once_with(city="Milwaukee ")

    @patch("users.views.get_weather_data")
    def test_get_weather_with_coords_success(self, mock_get_weather):
        self.client.login(username="testuser", password="test1234")

        mock_get_weather.return_value = {
            "city": "Somewhere",
            "temperature": 20,
            "conditions": "cloudy",
        }

        response = self.client.get(reverse("get_weather"), {"lat": "43.0", "lon": "-87.9"})
        self.assertEqual(response.status_code, 200)
        # called with floats
        mock_get_weather.assert_called_once_with(lat=43.0, lon=-87.9)

    def test_get_weather_missing_params_400(self):
        self.client.login(username="testuser", password="test1234")

        response = self.client.get(reverse("get_weather"))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "City or coordinates required")

    @patch("users.views.get_weather_data")
    def test_get_weather_api_failure_500(self, mock_get_weather):
        self.client.login(username="testuser", password="test1234")

        mock_get_weather.return_value = None
        response = self.client.get(reverse("get_weather"), {"city": "Milwaukee "})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["error"], "Could not fetch weather data")

    # -------------------------
    # spotify_logout view
    # -------------------------
    def test_spotify_logout_post_logs_out(self):
        self.client.login(username="testuser", password="test1234")
        response = self.client.post(reverse("spotify_logout"))
        self.assertRedirects(response, reverse("login_page"))

        # verify logged out by hitting a login_required page
        response2 = self.client.get(reverse("dashboard"))
        self.assertEqual(response2.status_code, 302)

    def test_spotify_logout_get_redirects_to_dashboard(self):
        self.client.login(username="testuser", password="test1234")
        response = self.client.get(reverse("spotify_logout"))
        self.assertRedirects(response, reverse("dashboard"))

    # -------------------------
    # password_change view
    # -------------------------
    def test_password_change_get_renders_form(self):
        self.client.login(username="testuser", password="test1234")
        response = self.client.get(reverse("password_change"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "password_change.html")
        self.assertIn("form", response.context)

    def test_password_change_post_success_redirects_profile(self):
        self.client.login(username="testuser", password="test1234")
        response = self.client.post(
            reverse("password_change"),
            {
                "old_password": "test1234",
                "new_password1": "NewPass123",
                "new_password2": "NewPass123",
            },
        )
        self.assertRedirects(response, reverse("profile"))

        # ensure new password works
        self.client.logout()
        self.assertTrue(self.client.login(username="testuser", password="NewPass123"))

    def test_password_change_post_failure_renders_with_errors(self):
        self.client.login(username="testuser", password="test1234")
        response = self.client.post(
            reverse("password_change"),
            {
                "old_password": "WRONG",
                "new_password1": "NewPass123",
                "new_password2": "NewPass123",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "password_change.html")
        self.assertIn("form", response.context)
        self.assertTrue(response.context["form"].errors)


    # -------------------------
    # signup_page view
    # -------------------------
    def test_signup_get_renders(self):
        response = self.client.get(reverse("signup_page"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "signup.html")

    def test_signup_redirects_if_authenticated(self):
        self.client.login(username="testuser", password="test1234")
        response = self.client.get(reverse("signup_page"))
        self.assertRedirects(response, reverse("dashboard"))

    def test_signup_post_success_creates_user_and_redirects(self):
        response = self.client.post(
            reverse("signup_page"),
            {
                "username": "newuser",
                "email": "new@example.com",
                "password1": "Pass123",
                "password2": "Pass123",
            },
        )
        self.assertRedirects(response, reverse("dashboard"))
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_signup_post_password_mismatch(self):
        response = self.client.post(
            reverse("signup_page"),
            {
                "username": "newuser2",
                "email": "new2@example.com",
                "password1": "Pass123",
                "password2": "DifferentPass123",
            },
        )
        self.assertRedirects(response, reverse("signup_page"))
        self.assertFalse(User.objects.filter(username="newuser2").exists())

    def test_signup_post_username_taken(self):
        response = self.client.post(
            reverse("signup_page"),
            {
                "username": "testuser",
                "email": "dup@example.com",
                "password1": "Pass123",
                "password2": "Pass123",
            },
        )
        self.assertRedirects(response, reverse("signup_page"))


    # -------------------------
    # profile_page view
    # -------------------------

    def test_profile_page_requires_login(self):
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 302)

    def test_profile_page_renders_with_context(self):
        self.client.login(username="testuser", password="test1234")

        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profile.html")

        self.assertEqual(response.context["username"], "testuser")
        self.assertEqual(response.context["email"], "test@example.com")
        self.assertIn("spotify_linked", response.context)
        self.assertIn("display_name", response.context)
        
        
    # -------------------------
    # generate_playlist view
    # -------------------------

    @patch("users.views.get_valid_spotify_client")
    @patch("users.views.get_weather_data")
    @patch("users.views.map_weather_to_mood")
    def test_generate_playlist_basic_flow(
        self, mock_weather_map, mock_weather, mock_spotify_client
    ):
        self.client.login(username="testuser", password="test1234")

        mock_sp = MagicMock()

        mock_sp.search.return_value = {
            "tracks": {
                "items": [
                    {
                        "name": "Test Song",
                        "uri": "spotify:track:123",
                        "artists": [{"name": "Artist"}],
                    }
                ]
            }
        }

        mock_sp._post.side_effect = [
            {"id": "playlist123", "external_urls": {"spotify": "http://spotify.com/test"}},
            {},
        ]

        mock_sp.tracks.return_value = {
            "tracks": [{"artists": [{"id": "artist123"}]}]
        }

        mock_sp.artist.return_value = {"genres": ["pop"]}

        mock_spotify_client.return_value = mock_sp

        mock_weather.return_value = {"conditions": "clear"}
        mock_weather_map.return_value = "sunny"

        SpotifyToken.objects.create(
            user=self.user,
            access_token="ACCESS",
            refresh_token="REFRESH",
            expires_at=9999999999,
        )

        response = self.client.post(
            reverse("generate_playlist"),
            {
                "playlist_name": "Test Playlist",
                "track_count": 10,
                "energy": 5,
                "happiness": 5,
                "danceability": 5,
                "activity": "chill",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("url", response.json())

        from users.models import Playlist
        self.assertTrue(Playlist.objects.filter(name="Test Playlist").exists())


    @patch("users.views.get_valid_spotify_client")
    def test_generate_playlist_without_spotify_token_redirects(self, mock_spotify):
        self.client.login(username="testuser", password="test1234")

        mock_spotify.side_effect = SpotifyToken.DoesNotExist

        response = self.client.post(reverse("generate_playlist"))

        self.assertEqual(response.status_code, 302)

    # -------------------------
    # get_location_suggest view
    # -------------------------

    @patch("users.views.get_location_suggestions")
    def test_location_suggest(self, mock_suggest):
        self.client.login(username="testuser", password="test1234")

        mock_suggest.return_value = ["Milwaukee", "Madison"]

        response = self.client.get(reverse("get_location_suggest"), {"q": "Mi"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["suggestions"], ["Milwaukee", "Madison"])    

    # -------------------------
    # delete_account view
    # -------------------------

    def test_delete_account_post(self):
        self.client.login(username="testuser", password="test1234")

        response = self.client.post(reverse("delete_account"))
        self.assertRedirects(response, reverse("login_page"))

        self.assertFalse(User.objects.filter(username="testuser").exists())