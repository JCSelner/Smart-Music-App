from django.contrib.auth.models import AbstractUser, User
from django.conf import settings
from django.db import models

# Create your models here.

class User(AbstractUser):
    USER_ROLE_CHOICES = [
    ("user", "User"),
    ("admin", "Admin"),
    ]
    role = models.CharField(max_length=20, choices=USER_ROLE_CHOICES, default="user")
    display_name = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.username} ({self.role})"

# Links Spotify login to account rather than session

class SpotifyToken(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    access_token = models.TextField()
    refresh_token = models.TextField()
    expires_at = models.IntegerField()

class Playlist(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="playlists"
    )

    name = models.CharField(max_length=255)
    spotify_url = models.URLField()
    track_count = models.IntegerField()

    mood = models.CharField(max_length=50, blank=True)
    genre = models.CharField(max_length=100, blank=True)
    weather_context = models.CharField(max_length=50, blank=True)
    visibility = models.CharField(max_length=10, default="private")

    # Influence fields — stored at generation time so history cards are self-contained
    energy = models.IntegerField(null=True, blank=True)           
    happiness = models.IntegerField(null=True, blank=True)        
    danceability = models.IntegerField(null=True, blank=True)     
    weather_label = models.CharField(max_length=100, blank=True)  
    weather_used = models.BooleanField(default=False)
    history_used = models.BooleanField(default=False)
    location_label = models.CharField(max_length=100, blank=True)  

    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"


class Feedback(models.Model):
    SUBJECT_CHOICES = [
        ("bug", "Bug Report"),
        ("suggestion", "Suggestion"),
        ("comment", "Comment"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="feedback"
    )
    subject = models.CharField(max_length=20, choices=SUBJECT_CHOICES)
    topic = models.CharField(max_length=255)
    description = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.get_subject_display()}] {self.topic} — {self.user.username}"