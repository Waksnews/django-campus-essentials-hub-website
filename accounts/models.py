# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('student', 'Student'),
        ('tutor', 'Tutor'),
        ('service_provider', 'Service Provider'),
        ('admin', 'Administrator'),
    )

    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True)
    student_id = models.CharField(max_length=20, blank=True)
    university = models.CharField(max_length=200, blank=True)
    course = models.CharField(max_length=100, blank=True)
    year_of_study = models.IntegerField(blank=True, null=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='student')
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True)
    bio = models.TextField(blank=True)
    points = models.IntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, blank=True)
    dark_mode = models.BooleanField(default=False)
    location = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} ({self.email})"

    class Meta:
        ordering = ['-date_joined']


class Badge(models.Model):
    BADGE_TYPES = (
        ('tutor', 'Top Tutor'),
        ('helper', 'Helpful Hero'),
        ('finder', 'Finder Star'),
        ('active', 'Active User'),
        ('expert', 'Subject Expert'),
        ('verified', 'Verified User'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='badges')
    badge_type = models.CharField(max_length=20, choices=BADGE_TYPES)
    awarded_date = models.DateTimeField(default=timezone.now)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['-awarded_date']

    def __str__(self):
        return f"{self.user.username} - {self.get_badge_type_display()}"