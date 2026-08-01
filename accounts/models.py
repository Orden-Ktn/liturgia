from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('cure', 'Curé'),
        ('secretaire', 'Secrétaire'),
        ('vicaire', 'Vicaire'),
        ('stagiaire', 'Stagiaire'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    EMAIL_FIELD = None
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username
    

