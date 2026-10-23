from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ("DOCTOR", "Doctor"),
        ("PATIENT", "Patient"),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="PATIENT")
    # Optional Google integration fields (nullable until user connects their Google account)
    google_refresh_token = models.TextField(null=True, blank=True)
    google_email = models.EmailField(null=True, blank=True)
