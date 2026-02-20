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
    # simple pages tests (generate, playlists, preferences)
    # -------------------------
    def test_generate_requires_login(self):
        response = self.client.get(reverse("generate"))
        self.assertEqual(response.status_code, 302)

    def test_generate_renders_when_logged_in(self):
        self.client.login(username="testuser", password="test1234")
        response = self.client.get(reverse("generate"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "generate.html")

    def test_playlists_renders_when_logged_in(self):
        self.client.login(username="testuser", password="test1234")
        response = self.client.get(reverse("playlists"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "playlists.html")

    def test_preferences_renders_when_logged_in(self):
        self.client.login(username="testuser", password="test1234")
        response = self.client.get(reverse("preferences"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "preferences.html")


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
    
    # Just a basic test to check it renders for logged in users. Detailed tests will be added 
    #once we have more functionality on the profile page.
        
    # -------------------------
    # generate_playlist view
    # -------------------------

    # This is should be very basic test just to check the flow.  