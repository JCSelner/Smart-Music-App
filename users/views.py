from django.shortcuts import render, redirect
from django.http import JsonResponse
from .spotify_utils import get_spotify_oauth
import spotipy

# Create your views here.

def home(request):
    return render(request, 'login.html')

def spotify_login(request):
    sp_oauth = get_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

def spotify_callback(request):
    sp_oauth = get_spotify_oauth()
    code = request.GET.get("code")
    token_info = sp_oauth.get_access_token(code)

    request.session["spotify_token"] = token_info
    return redirect("spotify_profile")

def spotify_profile(request):
    token_info = request.session.get("spotify_token")

    if not token_info:
        return redirect("spotify_login")

    sp = spotipy.Spotify(auth=token_info["access_token"])
    user = sp.current_user()

    return JsonResponse(user)