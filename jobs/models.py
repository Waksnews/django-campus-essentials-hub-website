from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.urls import reverse
from accounts.models import CustomUser


class Job(models.Model):
    CATEGORY_CHOICES = (
        ('typing', 'Typing Work'),
        ('design', 'Design'),
        ('errands', 'Errands'),
        ('academic', 'Academic Support'),
        ('photography', 'Photography'),
        ('tutoring', 'Tutoring'),
        ('tech', 'Tech Support'),
        ('writing', 'Writing'),
        ('other', 'Other'),
    )

    STATUS_CHOICES = (
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='posted_jobs')
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    location = models.CharField(max_length=200)
    budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    budget_type = models.CharField(max_length=20, choices=[('fixed', 'Fixed'), ('hourly', 'Hourly')])
    duration = models.CharField(max_length=100, blank=True)
    skills_required = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    is_remote = models.BooleanField(default=False, verbose_name="Remote work available")
    application_deadline = models.DateField(null=True, blank=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    views_count = models.PositiveIntegerField(default=0, editable=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"

    def is_active(self):
        if self.status != 'open':
            return False
        if self.application_deadline and timezone.now().date() > self.application_deadline:
            return False
        return True

    def increment_views(self):
        self.views_count += 1
        self.save(update_fields=['views_count'])

    def get_absolute_url(self):
        return reverse('jobs:detail', kwargs={'pk': self.pk})

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['category', 'status']),
        ]


class JobApplication(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    )

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='job_applications')
    cover_letter = models.TextField()
    proposed_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0.01)]
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applicant_message = models.TextField(blank=True)
    attachments = models.FileField(upload_to='job_applications/%Y/%m/%d/', blank=True, null=True)
    applied_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Application by {self.applicant.username} for {self.job.title}"

    def can_be_withdrawn(self):
        return self.status in ['pending', 'accepted']

    def get_status_color(self):
        status_colors = {
            'pending': 'warning',
            'accepted': 'success',
            'rejected': 'danger',
            'withdrawn': 'secondary',
        }
        return status_colors.get(self.status, 'secondary')

    class Meta:
        ordering = ['-applied_at']
        unique_together = ['job', 'applicant']
        indexes = [
            models.Index(fields=['status', 'applied_at']),
        ]