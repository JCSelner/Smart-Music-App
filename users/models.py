from django.contrib.auth.models import AbstractUser
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
