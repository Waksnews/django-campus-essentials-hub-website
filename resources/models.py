# resources/models.py
from django.db import models
from django.utils import timezone
from accounts.models import CustomUser


class Resource(models.Model):
    TYPE_CHOICES = (
        ('notes', 'Notes'),
        ('past_paper', 'Past Paper'),
        ('slides', 'Slides'),
        ('textbook', 'Textbook'),
        ('assignment', 'Assignment'),
        ('other', 'Other'),
    )

    SUBJECT_CHOICES = (
        ('programming', 'Programming'),
        ('mathematics', 'Mathematics'),
        ('physics', 'Physics'),
        ('chemistry', 'Chemistry'),
        ('biology', 'Biology'),
        ('business', 'Business'),
        ('engineering', 'Engineering'),
        ('languages', 'Languages'),
        ('arts', 'Arts & Humanities'),
        ('other', 'Other'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='uploaded_resources')
    title = models.CharField(max_length=200)
    description = models.TextField()
    resource_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    subject = models.CharField(max_length=100, choices=SUBJECT_CHOICES)
    course_code = models.CharField(max_length=20)
    file = models.FileField(upload_to='resources/')
    thumbnail = models.ImageField(upload_to='resource_thumbs/', blank=True)
    downloads = models.IntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.title} - {self.get_resource_type_display()}"

    class Meta:
        ordering = ['-created_at']


class ResourceReview(models.Model):
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='resource_reviews')
    rating = models.IntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['resource', 'user']