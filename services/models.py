# services/models.py
from django.db import models
from django.utils import timezone
from accounts.models import CustomUser


class Service(models.Model):
    CATEGORY_CHOICES = (
        ('printing', 'Printing & Photocopy'),
        ('repair', 'Phone/Device Repair'),
        ('laundry', 'Laundry'),
        ('food', 'Food & Drinks'),
        ('stationery', 'Stationery'),
        ('accommodation', 'Accommodation'),
        ('transport', 'Transport'),
        ('other', 'Other'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    location = models.CharField(max_length=200)
    contact_number = models.CharField(max_length=20)
    contact_email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    opening_hours = models.TextField()
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    price_range = models.CharField(max_length=50, blank=True)
    is_verified = models.BooleanField(default=False)
    qr_code = models.ImageField(upload_to='service_qr/', blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']


class ServiceReview(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='service_reviews')
    rating = models.IntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']