import os
import requests
from django.conf import settings

OPENWEATHERMAP_URL = "https://api.openweathermap.org/data/2.5/weather"

def get_weather_data(*,city=None, lat=None, lon=None, units="imperial"):
    api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    
    params = {
        "q": city,
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": units
    }
    
    try:
        response = requests.get(OPENWEATHERMAP_URL, params=params, timeout=10)
        response.raise_for_status()
        weather_data = response.json()
    except requests.RequestException as exc:
        print(f"Error fetching weather data")
        return None
    
    data = weather_data.get("main", {})
    weather = weather_data.get("weather", [])
    wind = weather_data.get("wind", {})

    return {
        "temperature": data.get("temp"),
        "conditions": weather[0].get("description") if weather else None,
        "humidity": data.get("humidity"),
        "wind_speed": wind.get("speed"),
    }