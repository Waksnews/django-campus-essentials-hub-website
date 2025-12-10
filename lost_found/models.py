# lost_found/models.py
from django.db import models
from django.utils import timezone
from accounts.models import CustomUser


class LostItem(models.Model):
    STATUS_CHOICES = (
        ('lost', 'Lost'),
        ('found', 'Found'),
        ('returned', 'Returned'),
        ('claimed', 'Claimed'),
    )

    CATEGORY_CHOICES = (
        ('electronics', 'Electronics'),
        ('documents', 'Documents'),
        ('clothing', 'Clothing'),
        ('accessories', 'Accessories'),
        ('books', 'Books'),
        ('keys', 'Keys'),
        ('wallet', 'Wallet/Purse'),
        ('other', 'Other'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='lost_items')
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='lost')
    location_lost = models.CharField(max_length=200)
    location_found = models.CharField(max_length=200, blank=True)
    date_lost = models.DateField()
    date_found = models.DateField(blank=True, null=True)
    image = models.ImageField(upload_to='lost_found/', blank=True)
    contact_info = models.CharField(max_length=200)
    is_resolved = models.BooleanField(default=False)
    reward = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['category']),
        ]


class FoundItem(models.Model):
    lost_item = models.ForeignKey(LostItem, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='found_matches')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='found_items')
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=LostItem.CATEGORY_CHOICES)
    location_found = models.CharField(max_length=200)
    date_found = models.DateField()
    image = models.ImageField(upload_to='lost_found/', blank=True)
    contact_info = models.CharField(max_length=200)
    is_claimed = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - Found"

    class Meta:
        ordering = ['-date_found']