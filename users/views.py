from django.shortcuts import redirect, render
from django.contrib.auth import get_user_model, login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.urls import reverse
from .models import SpotifyToken
from .spotify_utils import get_spotify_oauth, create_playlist_for_user
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect
from django.contrib.auth.forms import PasswordChangeForm

from .weather_utils import get_weather_data

User = get_user_model()


# Spotify OAuth

def spotify_login(request):
    """Redirect user to Spotify login page"""
    sp_oauth = get_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)


def spotify_callback(request):
    """Handle Spotify callback and log in the Django user"""
    sp_oauth = get_spotify_oauth()
    code = request.GET.get("code")
    if not code:
        messages.error(request, "Spotify login failed")
        return redirect("login_page")

    token_info = sp_oauth.get_access_token(code)
    sp = spotipy.Spotify(auth=token_info["access_token"])
    spotify_user = sp.current_user()

    spotify_id = spotify_user.get("id")
    display_name = spotify_user.get("display_name") or spotify_id
    email = spotify_user.get("email")

    # Create or get Django user
    user, created = User.objects.get_or_create(
        username=spotify_id,
        defaults={
            "email": email or "",
            "role": "user",  # default role for Spotify users
        }
    )

    # For Spotify users, prevent Django password login
    if created:
        user.set_unusable_password()
        user.save()

    # Log user in
    login(request, user)

    # Save or update Spotify token
    SpotifyToken.objects.update_or_create(
        user=user,
        defaults={
            "access_token": token_info["access_token"],
            "refresh_token": token_info["refresh_token"],
            "expires_at": token_info["expires_at"],
        }
    )

    return redirect("dashboard")


# Django login

def django_login(request):
    """Log in with username/password"""
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid username or password")
            return redirect("login_page")
    else:
        return redirect("login_page")


# Dashboard / Logout / Login Page

@login_required
def dashboard(request):
    try:
        spotify_token = SpotifyToken.objects.get(user=request.user)
        sp = spotipy.Spotify(auth=spotify_token.access_token)
        spotify_user = sp.current_user()
        display_name = spotify_user.get("display_name") or request.user.username
        spotify_linked = True
    except SpotifyToken.DoesNotExist:
        display_name = request.user.username
        spotify_linked = False

    from datetime import datetime
    hour = datetime.now().hour
    if hour < 12:
        time_of_day = "morning"
    elif hour < 17:
        time_of_day = "afternoon"
    else:
        time_of_day = "evening"

    return render(request, "dashboard.html", {
        "display_name": display_name,
        "spotify_linked": spotify_linked,
        "time_of_day": time_of_day,
        "total_playlists": 0,        # replace later with real queryset count
        "top_genre": "—",            # replace later with Spotify data
        "favourite_mood": "—",       # replace later with real data
        "weather_icon": "🌤️",        # replace later with OpenWeatherMap
        "weather_temp": "—",
        "weather_condition": "—",
        "weather_location": "—",
        "weather_mood": "—",
        "recent_playlists": [],      # replace later with real queryset
    })

 #Weather Info
@login_required
def get_weather(request):
    city = request.GET.get("city")
    lat = request.GET.get("lat")
    lon = request.GET.get("lon")

    if city:
        weather = get_weather_data(city=city)
    elif lat and lon:
        weather = get_weather_data(lat=float(lat), lon=float(lon))
    else:
        return JsonResponse({"error": "City or coordinates required"}, status=400)
    
    if not weather:
        return JsonResponse({"error": "Could not fetch weather data"}, status=500)

    return JsonResponse(weather)


def spotify_logout(request):
    """Logout for both Spotify and Django users"""
    if request.method == "POST":
        logout(request)
        return redirect("login_page")
    return redirect("dashboard")


def login_page(request):
    """Show the login page (Spotify + Django)"""
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "login.html")

@login_required
def generate_page(request):
    try:
        spotify_token = SpotifyToken.objects.get(user=request.user)
        sp = spotipy.Spotify(auth=spotify_token.access_token)
        display_name = sp.current_user().get("display_name") or request.user.username
        spotify_linked = True
    except SpotifyToken.DoesNotExist:
        display_name = request.user.username
        spotify_linked = False

    return render(request, "generate.html", {
        "spotify_linked": spotify_linked,
        "display_name": display_name,
    })

@login_required
def playlists_page(request):
    return render(request, "playlists.html")

@login_required
def profile_page(request):
    user = request.user
    try:
        spotify_token = SpotifyToken.objects.get(user=request.user)
        sp = spotipy.Spotify(auth=spotify_token.access_token)
        spotify_user = sp.current_user()
        display_name = spotify_user.get("display_name") or request.user.username
        spotify_linked = True
    except SpotifyToken.DoesNotExist:
        display_name = request.user.username
        spotify_linked = False

    return render(request, "profile.html", {
        "display_name": display_name,
        "spotify_linked": spotify_linked,
        "email": user.email,
        "username": user.username,
        "role": getattr(user, "role", "user"),
        "spotify_connect_url": reverse("spotify_login"),
        "spotify_disconnect_url": reverse("spotify_logout"),
        "password_change_url": reverse("password_change"),
    })

@login_required
def password_change(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()  # this hashes and updates the password
            # Keeps the user logged in after password change
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, 'password_change.html', {'form': form})

# Playlist Generation

def generate_playlist(request):
    sp_oauth = SpotifyOAuth(
        client_id=settings.SPOTIFY_CLIENT_ID,
        client_secret=settings.SPOTIFY_CLIENT_SECRET,
        redirect_uri=settings.SPOTIFY_REDIRECT_URI,
        scope="user-top-read playlist-modify-public playlist-modify-private"
    )

    token_info = sp_oauth.get_cached_token()

    if not token_info:
        return redirect("spotify_login")  

    sp = spotipy.Spotify(auth=token_info["access_token"])
    top_tracks = sp.current_user_top_tracks(limit=10)
    track_uris = [track["uri"] for track in top_tracks["items"]]

    user_id = sp.current_user()["id"]

    playlist = sp.user_playlist_create(
        user=user_id,
        name="Smart Playlist",
        public=False
    )

    sp.playlist_add_items(playlist["id"], track_uris)

    return JsonResponse({
        "message": "Playlist created!",
        "url": playlist["external_urls"]["spotify"]
    })
    

def signup_page(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")

        if not username or not password1:
            messages.error(request, "Username and password are required.")
            return redirect("signup_page")

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect("signup_page")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect("signup_page")

        user = User.objects.create_user(username=username, email=email, password=password1)

        # If your User model has role:
        if hasattr(user, "role") and not user.role:
            user.role = "user"
            user.save()

        login(request, user)
        return redirect("dashboard")

    return render(request, "signup.html")
