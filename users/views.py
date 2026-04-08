from django.shortcuts import redirect, render
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from django.core.cache import cache
from users.models import User
from .models import SpotifyToken, Playlist
from .spotify_utils import get_spotify_oauth, get_valid_spotify_client
from .weather_utils import get_weather_data, map_weather_to_mood, get_location_suggestions
from .dataset_utils import recommend_tracks, get_audio_baseline
import spotipy
import random
from collections import Counter

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

    token_info = sp_oauth.get_access_token(code, check_cache=False)
    sp = spotipy.Spotify(auth=token_info["access_token"])
    spotify_user = sp.current_user()
    assert spotify_user is not None

    spotify_id = spotify_user.get("id")
    display_name = spotify_user.get("display_name") or spotify_id
    email = spotify_user.get("email")

    # Create or get Django user
    user, created = User.objects.get_or_create(
        username=spotify_id,
        defaults={
            "email": email or "",
            "role": "user",
            "display_name": display_name,
        }
    )

    # For Spotify users, prevent Django password login
    if created:
        user.set_unusable_password()
    else:
        user.display_name = display_name
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
    spotify_linked = SpotifyToken.objects.filter(user=request.user).exists()
    display_name = request.user.display_name or request.user.username

    from datetime import datetime
    hour = datetime.now().hour
    if hour < 12:
        time_of_day = "morning"
    elif hour < 17:
        time_of_day = "afternoon"
    else:
        time_of_day = "evening"

    all_playlists = Playlist.objects.filter(user=request.user).order_by("-created_at")
    recent_playlists = all_playlists[:6]
    total_playlists = all_playlists.count()
    favorite_mood = get_favorite_mood(request.user)
    top_genre = get_top_genre(request.user)

    return render(request, "dashboard.html", {
        "display_name": display_name,
        "spotify_linked": spotify_linked,
        "time_of_day": time_of_day,
        "total_playlists": total_playlists,        # replace later with real queryset count
        "top_genre": top_genre,            # replace later with Spotify data
        "favourite_mood": favorite_mood,       # replace later with real data
        "weather_icon": "🌤️",        # replace later with OpenWeatherMap
        "weather_temp": "—",
        "weather_condition": "—",
        "weather_location": "—",
        "weather_mood": "—",
        "recent_playlists": recent_playlists,      # replace later with real queryset
    })

def get_top_genre(user):
    genres = Playlist.objects.filter(user=user).values_list("genre", flat=True)
    genres = [g for g in genres if g]  # remove empty
    if not genres:
        return "—"
    return Counter(genres).most_common(1)[0][0]

def get_favorite_mood(user):
    moods = Playlist.objects.filter(user=user).values_list("mood", flat=True)
    moods = [m for m in moods if m]
    if not moods:
        return "—"
    return Counter(moods).most_common(1)[0][0]

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


@login_required
def get_location_suggest(request):
    query = request.GET.get("q", "").strip()

    if len(query) < 2:
        return JsonResponse({"suggestions": []})

    suggestions = get_location_suggestions(query, limit=5)
    return JsonResponse({"suggestions": suggestions})


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
    spotify_linked = SpotifyToken.objects.filter(user=request.user).exists()

    return render(request, "generate.html", {
        "spotify_linked": spotify_linked,
        "weather_icon": "🌤️",
        "weather_temp": "—",
        "weather_location": "Enter city",
        "activities": [],
    })

@login_required
def playlists_page(request):
    playlists = Playlist.objects.filter(user=request.user).order_by("-created_at")

    return render(request, "playlists.html", {
        "playlists": playlists,
    })

@login_required
def profile_page(request):
    user = request.user
    spotify_linked = SpotifyToken.objects.filter(user=request.user).exists()
    display_name = user.display_name or user.username

    return render(request, "profile.html", {
        "display_name": display_name,
        "spotify_linked": spotify_linked,
        "email": user.email,
        "username": user.username,
        "role": getattr(user, "role", "user"),
        "spotify_connect_url": reverse("spotify_login"),
        "spotify_disconnect_url": reverse("spotify_logout"),
        "password_change_url": reverse("password_change"),
        "delete_account_url": reverse("delete_account"),
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

@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, 'Your account was successfully deleted!')
        return redirect('login_page')
    return render(request, 'delete_account.html')

# Playlist Generation

@login_required
def generate_playlist(request):
    try:
        sp = get_valid_spotify_client(request.user)
    except SpotifyToken.DoesNotExist:
        return redirect("spotify_login")

    use_history = request.POST.get("use_history") == "on"
    use_weather = request.POST.get("use_weather") == "on"

    playlist_name = request.POST.get("playlist_name", "").strip() or "Smart Playlist"
    visibility = request.POST.get("visibility", "private")
    is_public = visibility == "public"

    try:
        track_count = int(request.POST.get("track_count", 20))
    except (TypeError, ValueError):
        track_count = 20
    track_count = max(10, min(track_count, 50))

    try:
        energy = int(request.POST.get("energy", 5))
        happiness = int(request.POST.get("happiness", 5))
        danceability = int(request.POST.get("danceability", 5))
    except (TypeError, ValueError):
        energy, happiness, danceability = 5, 5, 5

    activity = request.POST.get("activity", "chill")
    location = request.POST.get("location", "").strip()
    lat = request.POST.get("lat")
    lon = request.POST.get("lon")

    weather = None
    weather_features = None

    if use_weather:
        if location:
            weather = get_weather_data(city=location)
        elif lat and lon:
            weather = get_weather_data(lat=float(lat), lon=float(lon))

        if weather:
            weather_features = map_weather_to_mood(weather)

    # 1. Fetch user context for better recommendations
    user_genres = []
    baseline = None

    try:
        top_artists_resp = sp.current_user_top_artists(limit=20, time_range="short_term")
        top_artists = top_artists_resp.get("items", []) if top_artists_resp else []
        for artist in top_artists:
            artist_id = artist.get("id")
            if artist_id:
                cached = cache.get(f"artist_{artist_id}")
                genres = cached.get("genres", []) if cached else artist.get("genres", [])
                user_genres.extend(genres)
    except spotipy.SpotifyException:
        pass

    history_tracks = []
    top_items = []

    try:
        recent_resp = sp.current_user_recently_played(limit=50)
        recent_items = recent_resp.get("items", []) if recent_resp else []
        history_tracks += [
            (item["track"]["name"], item["track"]["artists"][0]["name"])
            for item in recent_items
            if item.get("track") and item["track"].get("artists")
        ]
    except spotipy.SpotifyException:
        pass

    try:
        top_tracks_resp = sp.current_user_top_tracks(limit=50, time_range="short_term")
        top_items = top_tracks_resp.get("items", []) if top_tracks_resp else []
        history_tracks += [
            (item["name"], item["artists"][0]["name"])
            for item in top_items
            if item.get("name") and item.get("artists")
        ]
    except spotipy.SpotifyException:
        pass

    baseline = get_audio_baseline(history_tracks) if history_tracks else None
    exclude_tracks = {item["name"].lower() for item in top_items if item.get("name")} if top_items else None

    # 2. Get dataset recommendations filtered by audio features
    candidates = recommend_tracks(
        energy, happiness, danceability,
        activity=activity,
        weather_features=weather_features,
        user_genres=user_genres or None,
        baseline=baseline,
        exclude_tracks=exclude_tracks,
        limit=80,
    )

    # 3. If using history, seed with user's top tracks
    seen_uris = set()
    final_uris = []

    if use_history:
        try:
            top_tracks = sp.current_user_top_tracks(limit=20, time_range="short_term")
            top_items = top_tracks.get("items", []) if top_tracks else []
        except spotipy.SpotifyException:
            top_items = []

        for item in top_items:
            uri = item.get("uri")
            if uri and uri not in seen_uris:
                seen_uris.add(uri)
                final_uris.append(uri)

    # 4. Resolve dataset candidates to Spotify URIs
    needed = track_count * 2
    for track_name, artist in candidates:
        if len(final_uris) >= needed:
            break
        cache_key = f"track_uri_{track_name}_{artist}"
        uri = cache.get(cache_key)
        if uri is None:
            query = f'track:"{track_name}" artist:"{artist}"'
            results = sp.search(q=query, type="track", limit=1)
            items = results.get("tracks", {}).get("items", [])
            uri = items[0].get("uri") if items else ""
            cache.set(cache_key, uri, timeout=None)
        if uri and uri not in seen_uris:
            seen_uris.add(uri)
            final_uris.append(uri)

    if not final_uris:
        return JsonResponse({"error": "No tracks found to build playlist."}, status=400)

    random.shuffle(final_uris)
    final_uris = final_uris[:track_count]

    # Create playlist
    playlist = sp._post(
        "me/playlists",
        payload={
            "name": playlist_name,
            "public": is_public,
            "description": "Generated by Smart Music App based on mood, weather, activity, and history",
        },
    )

    if not playlist or not playlist.get("id"):
        return JsonResponse({"error": "Failed to create Spotify playlist."}, status=500)

    sp._post(f"playlists/{playlist['id']}/items", payload={"uris": final_uris})

    track_genres = []

    try:
        tracks_response = sp.tracks(final_uris) or {}
        tracks_data = tracks_response.get("tracks", [])
        artist_ids = list({
            artist["id"]
            for track in tracks_data if track
            for artist in track.get("artists", [])
        })

        for artist_id in artist_ids:
            artist_info = cache.get(f"artist_{artist_id}")
            if artist_info is None:
                artist_info = sp.artist(artist_id) or {}
                cache.set(f"artist_{artist_id}", artist_info, timeout=None)
            track_genres.extend(artist_info.get("genres", []))
    except spotipy.SpotifyException:
        pass

    playlist_genre = Counter(track_genres).most_common(1)[0][0] if track_genres else ""

    Playlist.objects.create(
        user=request.user,
        name=playlist_name,
        spotify_url=playlist["external_urls"]["spotify"],
        track_count=len(final_uris),
        mood=activity,
        genre=playlist_genre,
        weather_context=weather_features if weather_features else "",
    )

    return JsonResponse({
        "message": "Playlist created!",
        "url": playlist["external_urls"]["spotify"],
        "used_history": use_history,
        "track_count": len(final_uris),
        "weather_features": weather_features,
        "activity": activity,
    })

@login_required
def delete_playlist(request, playlist_id):
    if request.method == "POST":
        playlist = Playlist.objects.get(id=playlist_id, user=request.user)

        try:
            sp = get_valid_spotify_client(request.user)
            spotify_id = playlist.spotify_url.split("/")[-1]
            sp.current_user_unfollow_playlist(spotify_id)
        except Exception as e:
            print("Spotify delete failed:", e)

        playlist.delete()
        return redirect("playlists")
    return redirect("playlists")


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
