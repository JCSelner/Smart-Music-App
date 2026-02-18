from django.contrib.auth.models import AbstractUser, User
from django.conf import settings
from django.db import models

# Create your models here.

class User(AbstractUser):
    USER_ROLE_CHOICES = [
        ("user", "User"),
        ("manager", "Manager"),
        ("admin", "Admin"),
    ]
    role = models.CharField(max_length=20, choices=USER_ROLE_CHOICES, default="user")

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

