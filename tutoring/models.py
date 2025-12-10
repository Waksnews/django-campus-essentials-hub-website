# tutoring/models.py
from django.db import models
from django.utils import timezone
from accounts.models import CustomUser


class Tutor(models.Model):
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

    LEVEL_CHOICES = (
        ('freshman', 'Freshman'),
        ('sophomore', 'Sophomore'),
        ('junior', 'Junior'),
        ('senior', 'Senior'),
        ('graduate', 'Graduate'),
    )

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='tutor_profile')
    subjects = models.CharField(max_length=200)  # comma-separated list
    primary_subject = models.CharField(max_length=50, choices=SUBJECT_CHOICES)
    year_of_study = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    hourly_rate = models.DecimalField(max_digits=6, decimal_places=2)
    bio = models.TextField()
    qualifications = models.TextField()
    availability = models.TextField()
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    total_sessions = models.IntegerField(default=0)
    is_available = models.BooleanField(default=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def update_total_sessions(self):
        self.total_sessions = self.sessions.filter(status='completed').count()
        self.save()

    def __str__(self):
        return f"{self.user.username} - {self.get_primary_subject_display()} Tutor"


class Session(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE, related_name='sessions')
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='booked_sessions')
    subject = models.CharField(max_length=100)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration = models.IntegerField()  # in minutes
    location = models.CharField(max_length=200)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Session: {self.tutor.user.username} with {self.student.username} on {self.date}"


class Review(models.Model):
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE, related_name='reviews')
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='tutor_reviews')
    rating = models.IntegerField()  # 1-5
    comment = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']