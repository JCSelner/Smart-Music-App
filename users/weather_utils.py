import os
import requests
from django.conf import settings

OPENWEATHERMAP_URL = "https://api.openweathermap.org/data/2.5/weather"

# def get_weather_data(*,city=None, lat=None, lon=None, units="imperial"):
#     api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    
#     params = {
#         "q": city,
#         "lat": lat,
#         "lon": lon,
#         "appid": api_key,
#         "units": units
#     }
    
#     try:
#         response = requests.get(OPENWEATHERMAP_URL, params=params, timeout=10)
#         response.raise_for_status()
#         weather_data = response.json()
#     except requests.RequestException as exc:
#         print(f"Error fetching weather data")
#         return None
    
#     data = weather_data.get("main", {})
#     weather = weather_data.get("weather", [])
#     wind = weather_data.get("wind", {})

#     return {
#         "city": weather_data.get("name"),
#         "temperature": data.get("temp"),
#         "conditions": weather[0].get("description") if weather else None,
#         "humidity": data.get("humidity"),
#         "wind_speed": wind.get("speed"),
#     }

def get_weather_data(*, city=None, lat=None, lon=None, units="imperial"):
    api_key = os.getenv("OPENWEATHERMAP_API_KEY")

    params = {
        "appid": api_key,
        "units": units,
    }

    if city:
        params["q"] = city
    elif lat is not None and lon is not None:
        params["lat"] = lat
        params["lon"] = lon
    else:
        print("Error: must provide either city or lat/lon")
        return None

    try:
        response = requests.get(OPENWEATHERMAP_URL, params=params, timeout=10)
        response.raise_for_status()
        weather_data = response.json()
    except requests.RequestException as exc:
        print(f"Error fetching weather data: {exc}")
        return None

    data = weather_data.get("main", {})
    weather = weather_data.get("weather", [])
    wind = weather_data.get("wind", {})

    return {
        "city": weather_data.get("name"),
        "temperature": data.get("temp"),
        "conditions": weather[0].get("description") if weather else None,
        "humidity": data.get("humidity"),
        "wind_speed": wind.get("speed"),
    }

def map_weather_to_mood(weather_data):
    condition = weather_data.get("conditions", "").lower()
    temp = weather_data.get("temperature", 70)

    adjustments = {
        "energy": 5,
        "happiness": 5,
        "danceability": 5,
    }

    if "rain" in condition or "storm" in condition:
        adjustments["energy"] = 3
        adjustments["happiness"] = 3 
        adjustments["danceability"] = 2
    elif "clear" in condition or "sunny" in condition:
        adjustments["energy"] = 8
        adjustments["happiness"] = 8
        adjustments["danceability"] = 8
    elif "cloudy" in condition or "overcast" in condition:
        adjustments["energy"] = 5
        adjustments["happiness"] = 5
        adjustments["danceability"] = 5
    elif "snow" in condition:
        adjustments["energy"] = 4
        adjustments["happiness"] = 6
        adjustments["danceability"] = 3

    if temp > 85:  # Hot
        adjustments["energy"] = min(10, adjustments["energy"] + 1)
        adjustments["danceability"] = min(10, adjustments["danceability"] + 1)
    elif temp < 32:  # Cold
        adjustments["energy"] = max(1, adjustments["energy"] - 1)
    
    return adjustments
    