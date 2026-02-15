from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models

# Create your models here.

class User(AbstractUser):
    ROLE_CHOICES = (
        ('user', 'Standard User'),
        ('manager', 'Manager'),
        ('admin', 'Administrator'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')

    def is_manager(self):
        return self.role == 'manager'

    def is_admin(self):
        return self.role == 'admin'

from django.contrib.auth.models import User
from django.db import models

# Links Spotify login to account rather than session

class SpotifyToken(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    access_token = models.TextField()
    refresh_token = models.TextField()
    expires_at = models.IntegerField()

