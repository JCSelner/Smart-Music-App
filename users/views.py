from .models import SpotifyToken
from .spotify_utils import get_spotify_oauth
from django.conf import settings
from django.contrib.auth import get_user_model, logout, login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect, render
import spotipy, time


User = get_user_model()

def spotify_login(request):
    sp_oauth = get_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

def spotify_callback(request):
    sp_oauth = get_spotify_oauth()
    code = request.GET.get("code")

    token_info = sp_oauth.get_access_token(code)

    sp = spotipy.Spotify(auth=token_info["access_token"])
    spotify_user = sp.current_user()

    spotify_id = spotify_user.get("id")
    display_name = spotify_user.get("display_name") or spotify_id
    email = spotify_user.get("email")

    # 🔹 Create or get Django user
    user, created = User.objects.get_or_create(
        username=spotify_id,
        defaults={
            "email": email or "",
            "role": "user"  # all Spotify logins are 'user' by default
        }
    )

    # 🔹 Log the Django user in
    login(request, user)

    # 🔹 Save or update Spotify token
    SpotifyToken.objects.update_or_create(
        user=user,
        defaults={
            "access_token": token_info["access_token"],
            "refresh_token": token_info["refresh_token"],
            "expires_at": token_info["expires_at"],
        }
    )

    return redirect("home")


def spotify_profile(request):
    token_info = request.session.get("spotify_token")

    if not token_info:
        return redirect("spotify_login")

    sp = spotipy.Spotify(auth=token_info["access_token"])
    user = sp.current_user()

    return JsonResponse(user)

@login_required
def home(request):
    return render(request, "home.html", {
        "display_name": request.user.username
    })

def spotify_logout(request):
    if request.method == "POST":
        logout(request)
        return redirect("login_page")  # back to login.html
    else:
        return redirect("home")  # prevent GET requests from logging out

def login_page(request):
    # If already logged in, go home
    if request.user.is_authenticated:
        return redirect("home")
    return render(request, "login.html")

def django_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "Invalid username or password")
            return redirect("login_page")
    else:
        return redirect("login_page")
