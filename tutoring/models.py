from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import CustomUser
import json


class Subject(models.Model):
    """Separate model for subjects to allow better filtering"""
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50)
    icon = models.CharField(max_length=50, default='fas fa-book')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"


class Tutor(models.Model):
    LEVEL_CHOICES = (
        ('freshman', 'Freshman'),
        ('sophomore', 'Sophomore'),
        ('junior', 'Junior'),
        ('senior', 'Senior'),
        ('graduate', 'Graduate'),
        ('phd', 'PhD Student'),
        ('alumni', 'Alumni'),
        ('professional', 'Professional'),
    )

    CONTACT_CHOICES = [
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('whatsapp', 'WhatsApp'),
        ('in_app', 'In-App Messaging')
    ]

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='tutor_profile')
    subjects = models.ManyToManyField(Subject, related_name='tutors', blank=True)
    primary_subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='primary_tutors')
    year_of_study = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='freshman')
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(5)], default=20.00)
    bio = models.TextField(max_length=1000, blank=True)
    qualifications = models.TextField(max_length=500, blank=True)
    teaching_experience = models.TextField(max_length=500, blank=True)

    # Availability - Use JSON field (simpler than separate model)
    availability = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON format: {'monday': [9,10,11], 'tuesday': [14,15,16], ...}"
    )

    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    total_reviews = models.IntegerField(default=0)
    total_sessions = models.IntegerField(default=0)
    total_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    is_available = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False, help_text="Verified by campus staff")
    profile_picture = models.ImageField(upload_to='tutor_profiles/', blank=True, null=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    # Contact preferences
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    preferred_contact = models.CharField(max_length=20, choices=CONTACT_CHOICES, default='in_app')

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.primary_subject.name if self.primary_subject else 'Tutor'}"

    def update_rating(self):
        """Recalculate average rating"""
        reviews = self.reviews.all()
        if reviews.exists():
            avg = reviews.aggregate(models.Avg('rating'))['rating__avg']
            self.rating = round(avg, 2) if avg else 0.0
            self.total_reviews = reviews.count()
            self.save(update_fields=['rating', 'total_reviews'])

    def get_availability_display(self):
        """Format availability for display"""
        if not self.availability:
            return "Not specified"

        days = {
            'monday': 'Monday', 'tuesday': 'Tuesday', 'wednesday': 'Wednesday',
            'thursday': 'Thursday', 'friday': 'Friday', 'saturday': 'Saturday',
            'sunday': 'Sunday'
        }

        available_days = []
        for day, hours in self.availability.items():
            if hours and isinstance(hours, list):
                day_name = days.get(day, day.capitalize())
                hours_str = ', '.join(f"{h}:00" for h in hours)
                available_days.append(f"{day_name}: {hours_str}")

        return ' | '.join(available_days) if available_days else "Not specified"

    def is_available_at(self, date, hour):
        """Check if tutor is available at specific date/time"""
        day_name = date.strftime('%A').lower()
        return hour in self.availability.get(day_name, [])

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username

    @property
    def profile_completion_percentage(self):
        """Calculate profile completion percentage"""
        total_fields = 8
        completed = 0

        if self.profile_picture: completed += 1
        if self.bio and len(self.bio) >= 100: completed += 1
        if self.qualifications: completed += 1
        if self.teaching_experience: completed += 1
        if self.contact_email or self.contact_phone: completed += 1
        if self.subjects.exists(): completed += 1
        if self.availability: completed += 1
        if self.hourly_rate > 0: completed += 1

        return int((completed / total_fields) * 100)

    class Meta:
        ordering = ['-rating', '-total_sessions']
        indexes = [
            models.Index(fields=['rating', 'is_available']),
            models.Index(fields=['hourly_rate', 'is_available']),
        ]
        verbose_name = "Tutor"
        verbose_name_plural = "Tutors"


class Session(models.Model):
    STATUS_CHOICES = [
        ('pending', '⏳ Pending'),
        ('confirmed', '✅ Confirmed'),
        ('completed', '🎓 Completed'),
        ('cancelled', '❌ Cancelled'),
        ('no_show', '🚫 No Show'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    ]

    LOCATION_CHOICES = [
        ('campus', 'On Campus'),
        ('online', 'Online'),
        ('library', 'Library'),
        ('other', 'Other Location')
    ]

    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE, related_name='sessions')
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='booked_sessions')
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions')

    # Date and time
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration = models.IntegerField(help_text="Duration in minutes", default=60)

    # Session details
    topic = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=20, choices=LOCATION_CHOICES, default='campus')
    location_details = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True, help_text="Specific topics or questions")

    # Status and payment
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    amount = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)], default=0.00)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=50, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True)

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    # Student rating after completion
    student_rating = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    student_feedback = models.TextField(blank=True)

    def __str__(self):
        return f"Session: {self.tutor.user.username} with {self.student.username} on {self.date}"

    def save(self, *args, **kwargs):
        # Auto-calculate duration if not set
        if self.start_time and self.end_time and not self.duration:
            from datetime import datetime
            start = datetime.combine(self.date, self.start_time)
            end = datetime.combine(self.date, self.end_time)
            self.duration = (end - start).seconds // 60

        # Auto-calculate amount if not set
        if not self.amount and self.tutor and self.duration:
            hours = self.duration / 60
            self.amount = round(hours * self.tutor.hourly_rate, 2)

        # Update timestamps based on status
        if self.status == 'confirmed' and not self.confirmed_at:
            self.confirmed_at = timezone.now()
        elif self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
            # Update tutor stats
            self.tutor.total_sessions += 1
            self.tutor.total_hours += self.duration / 60
            self.tutor.save(update_fields=['total_sessions', 'total_hours'])
        elif self.status == 'cancelled' and not self.cancelled_at:
            self.cancelled_at = timezone.now()

        super().save(*args, **kwargs)

    @property
    def is_upcoming(self):
        from django.utils import timezone
        from datetime import datetime
        session_datetime = datetime.combine(self.date, self.start_time)
        return session_datetime > timezone.now() and self.status in ['pending', 'confirmed']

    @property
    def is_past(self):
        from django.utils import timezone
        from datetime import datetime
        session_datetime = datetime.combine(self.date, self.start_time)
        return session_datetime < timezone.now()

    @property
    def datetime(self):
        from datetime import datetime
        return datetime.combine(self.date, self.start_time)

    class Meta:
        ordering = ['-date', '-start_time']
        unique_together = ['tutor', 'date', 'start_time']
        indexes = [
            models.Index(fields=['tutor', 'status', 'date']),
            models.Index(fields=['student', 'status', 'date']),
        ]
        verbose_name = "Session"
        verbose_name_plural = "Sessions"


class Review(models.Model):
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE, related_name='reviews')
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='tutor_reviews')
    session = models.OneToOneField(Session, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='session_review')

    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], default=5)
    comment = models.TextField(max_length=1000, blank=True)

    # Review categories (1-5 for each)
    knowledge = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], default=5)
    teaching_skill = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], default=5)
    communication = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], default=5)
    punctuality = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], default=5)

    is_verified = models.BooleanField(default=False, help_text="Review from actual session")
    helpful_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Review by {self.student.username} for {self.tutor.user.username}"

    def save(self, *args, **kwargs):
        # Mark as verified if linked to a completed session
        if self.session and self.session.status == 'completed':
            self.is_verified = True

        super().save(*args, **kwargs)

        # Update tutor's overall rating
        self.tutor.update_rating()

    @property
    def average_category_rating(self):
        return (self.knowledge + self.teaching_skill + self.communication + self.punctuality) / 4

    class Meta:
        ordering = ['-created_at']
        unique_together = ['tutor', 'student']
        verbose_name = "Tutor Review"
        verbose_name_plural = "Tutor Reviews"


class TutorApplication(models.Model):
    """Track tutor applications"""
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('more_info', 'Needs More Info'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='tutor_applications')
    subjects = models.CharField(max_length=500)
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2)
    bio = models.TextField()
    qualifications = models.TextField()
    experience = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True)
    applied_at = models.DateTimeField(default=timezone.now)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='reviewed_applications')

    def __str__(self):
        return f"Application by {self.user.username} - {self.get_status_display()}"

    class Meta:
        ordering = ['-applied_at']
        verbose_name = "Tutor Application"
        verbose_name_plural = "Tutor Applications"