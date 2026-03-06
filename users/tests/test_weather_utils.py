from django.test import TestCase
from unittest.mock import patch, MagicMock
from users.weather_utils import get_weather_data
import requests


# Reusable fake API response
def make_mock_response(city="Milwaukee", temp=72, description="clear sky", humidity=50, wind_speed=5.5):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "name": city,
        "main": {"temp": temp, "humidity": humidity},
        "weather": [{"description": description}],
        "wind": {"speed": wind_speed},
    }
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


class GetWeatherDataTests(TestCase):

    # -------------------------
    # Successful calls
    # -------------------------

    @patch("users.weather_utils.requests.get")
    def test_returns_dict_with_expected_keys(self, mock_get):
        mock_get.return_value = make_mock_response()
        result = get_weather_data(city="Milwaukee")

        self.assertIsNotNone(result)
        for key in ("city", "temperature", "conditions", "humidity", "wind_speed"):
            self.assertIn(key, result)

    @patch("users.weather_utils.requests.get")
    def test_city_query_returns_correct_values(self, mock_get):
        mock_get.return_value = make_mock_response(city="Milwaukee", temp=65, description="light rain")
        result = get_weather_data(city="Milwaukee")

        self.assertEqual(result["city"], "Milwaukee")
        self.assertEqual(result["temperature"], 65)
        self.assertEqual(result["conditions"], "light rain")

    @patch("users.weather_utils.requests.get")
    def test_lat_lon_query_calls_api(self, mock_get):
        mock_get.return_value = make_mock_response(city="Somewhere")
        result = get_weather_data(lat=43.0, lon=-87.9)

        self.assertIsNotNone(result)
        # lat/lon should be passed in the params
        call_kwargs = mock_get.call_args
        params = call_kwargs[1]["params"] if call_kwargs[1] else call_kwargs[0][1]
        self.assertEqual(params["lat"], 43.0)
        self.assertEqual(params["lon"], -87.9)

    @patch("users.weather_utils.requests.get")
    def test_humidity_and_wind_returned(self, mock_get):
        mock_get.return_value = make_mock_response(humidity=80, wind_speed=12.3)
        result = get_weather_data(city="Chicago")

        self.assertEqual(result["humidity"], 80)
        self.assertEqual(result["wind_speed"], 12.3)

    @patch("users.weather_utils.requests.get")
    def test_empty_weather_list_returns_none_conditions(self, mock_get):
        """API response with no weather array should not crash."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "name": "Ghost Town",
            "main": {"temp": 50, "humidity": 40},
            "weather": [],   # <-- empty
            "wind": {"speed": 3.0},
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = get_weather_data(city="Ghost Town")
        self.assertIsNotNone(result)
        self.assertIsNone(result["conditions"])

    # -------------------------
    # Error / failure cases
    # -------------------------

    @patch("users.weather_utils.requests.get")
    def test_returns_none_on_request_exception(self, mock_get):
        mock_get.side_effect = requests.RequestException("timeout")
        result = get_weather_data(city="BadCity")
        self.assertIsNone(result)

    @patch("users.weather_utils.requests.get")
    def test_returns_none_on_http_error(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = requests.HTTPError("404")
        mock_get.return_value = mock_resp

        result = get_weather_data(city="NoWhere")
        self.assertIsNone(result)

    @patch("users.weather_utils.requests.get")
    def test_default_units_are_imperial(self, mock_get):
        mock_get.return_value = make_mock_response()
        get_weather_data(city="Milwaukee")

        call_kwargs = mock_get.call_args
        params = call_kwargs[1]["params"] if call_kwargs[1] else call_kwargs[0][1]
        self.assertEqual(params["units"], "imperial")

    @patch("users.weather_utils.requests.get")
    def test_custom_units_passed_through(self, mock_get):
        mock_get.return_value = make_mock_response()
        get_weather_data(city="London", units="metric")

        call_kwargs = mock_get.call_args
        params = call_kwargs[1]["params"] if call_kwargs[1] else call_kwargs[0][1]
        self.assertEqual(params["units"], "metric")