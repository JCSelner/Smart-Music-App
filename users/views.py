from django.shortcuts import redirect, render
from django.contrib.auth import get_user_model, login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from .models import SpotifyToken
from .spotify_utils import get_spotify_oauth
import spotipy

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

    return redirect("home")


# # Optional: show Spotify profile info (JSON)
# def spotify_profile(request):
#     token_info = request.session.get("spotify_token")
#     if not token_info:
#         return redirect("spotify_login")
#     sp = spotipy.Spotify(auth=token_info["access_token"])
#     user = sp.current_user()
#     return JsonResponse(user)


# Django login

def django_login(request):
    """Log in with username/password"""
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


# Home / Logout / Login Page

@login_required
def home(request):
    """Home page after login (Spotify or Django)"""
    # Show Spotify display name if available
    try:
        spotify_token = SpotifyToken.objects.get(user=request.user)
        sp = spotipy.Spotify(auth=spotify_token.access_token)
        spotify_user = sp.current_user()
        display_name = spotify_user.get("display_name") or request.user.username
    except SpotifyToken.DoesNotExist:
        display_name = request.user.username

    return render(request, "home.html", {
        "display_name": display_name,
        "role": request.user.role
    })


def spotify_logout(request):
    """Logout for both Spotify and Django users"""
    if request.method == "POST":
        logout(request)
        return redirect("login_page")
    return redirect("home")


def login_page(request):
    """Show the login page (Spotify + Django)"""
    if request.user.is_authenticated:
        return redirect("home")
    return render(request, "login.html")
