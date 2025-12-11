from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
from accounts.models import CustomUser


class Resource(models.Model):
    TYPE_CHOICES = (
        ('notes', '📝 Notes'),
        ('past_paper', '📄 Past Paper'),
        ('slides', '📊 Slides'),
        ('textbook', '📚 Textbook'),
        ('assignment', '📋 Assignment'),
        ('project', '💼 Project'),
        ('code', '💻 Code'),
        ('video', '🎥 Video'),
        ('other', '📦 Other'),
    )

    SUBJECT_CHOICES = (
        ('programming', '💻 Programming'),
        ('mathematics', '🧮 Mathematics'),
        ('physics', '⚛️ Physics'),
        ('chemistry', '🧪 Chemistry'),
        ('biology', '🧬 Biology'),
        ('business', '💼 Business'),
        ('engineering', '⚙️ Engineering'),
        ('languages', '🗣️ Languages'),
        ('arts', '🎨 Arts & Humanities'),
        ('social_sciences', '🌍 Social Sciences'),
        ('health', '🏥 Health Sciences'),
        ('other', '📚 Other'),
    )

    ACCESS_CHOICES = (
        ('public', 'Public'),
        ('campus_only', 'Campus Only'),
        ('private', 'Private'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='uploaded_resources')
    title = models.CharField(max_length=200)
    description = models.TextField()
    resource_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    subject = models.CharField(max_length=100, choices=SUBJECT_CHOICES)
    course_code = models.CharField(max_length=20, help_text="e.g., CS101, MATH202")
    course_name = models.CharField(max_length=100, blank=True, help_text="Optional: Full course name")
    file = models.FileField(upload_to='resources/%Y/%m/%d/')
    thumbnail = models.ImageField(upload_to='resource_thumbs/%Y/%m/%d/', blank=True, null=True)
    file_size = models.BigIntegerField(default=0, editable=False)  # in bytes
    downloads = models.PositiveIntegerField(default=0, editable=False)
    views = models.PositiveIntegerField(default=0, editable=False)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0, editable=False)
    total_ratings = models.PositiveIntegerField(default=0, editable=False)
    access_level = models.CharField(max_length=20, choices=ACCESS_CHOICES, default='public')
    is_approved = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    tags = models.CharField(max_length=255, blank=True, help_text="Comma-separated tags")
    year = models.PositiveIntegerField(null=True, blank=True, help_text="Year of resource (e.g., 2023)")
    semester = models.CharField(max_length=20, blank=True, choices=[
        ('', 'Not specified'),
        ('fall', 'Fall'),
        ('spring', 'Spring'),
        ('summer', 'Summer'),
        ('winter', 'Winter'),
    ])
    instructor = models.CharField(max_length=100, blank=True, help_text="Course instructor/professor")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.get_resource_type_display()}"

    def get_absolute_url(self):
        return reverse('resources:detail', kwargs={'pk': self.pk})

    def get_file_size_display(self):
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} TB"

    def increment_downloads(self):
        self.downloads += 1
        self.save(update_fields=['downloads'])

    def increment_views(self):
        self.views += 1
        self.save(update_fields=['views'])

    def update_rating(self, new_rating):
        """Update average rating when new review is added"""
        total_score = (self.average_rating * self.total_ratings) + new_rating
        self.total_ratings += 1
        self.average_rating = total_score / self.total_ratings
        self.save(update_fields=['average_rating', 'total_ratings'])

    def get_rating_stars(self):
        """Return HTML for star ratings"""
        full_stars = int(self.average_rating)
        half_star = self.average_rating - full_stars >= 0.5
        empty_stars = 5 - full_stars - (1 if half_star else 0)

        stars = '★' * full_stars
        stars += '½' if half_star else ''
        stars += '☆' * empty_stars

        return stars

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['resource_type', 'is_approved']),
            models.Index(fields=['subject', 'is_approved']),
            models.Index(fields=['average_rating', 'downloads']),
        ]
        verbose_name = "Resource"
        verbose_name_plural = "Resources"


class ResourceReview(models.Model):
    RATING_CHOICES = [
        (1, '1 Star - Poor'),
        (2, '2 Stars - Fair'),
        (3, '3 Stars - Good'),
        (4, '4 Stars - Very Good'),
        (5, '5 Stars - Excellent'),
    ]

    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='resource_reviews')
    rating = models.IntegerField(choices=RATING_CHOICES, validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    helpful = models.PositiveIntegerField(default=0, editable=False)
    not_helpful = models.PositiveIntegerField(default=0, editable=False)
    is_verified = models.BooleanField(default=False, help_text="Verified downloader")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Review by {self.user.username} for {self.resource.title}"

    def get_rating_stars(self):
        """Return HTML stars for this review"""
        return '★' * self.rating + '☆' * (5 - self.rating)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['resource', 'user']
        verbose_name = "Resource Review"
        verbose_name_plural = "Resource Reviews"


class ResourceDownload(models.Model):
    """Track detailed download information"""
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='download_history')
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='downloads')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    downloaded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-downloaded_at']


class ResourceBookmark(models.Model):
    """Allow users to bookmark resources"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='bookmarked_resources')
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='bookmarks')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['user', 'resource']
        ordering = ['-created_at']
        verbose_name = "Bookmark"
        verbose_name_plural = "Bookmarks"