from django.contrib import admin
from .models import Subject, Tutor, Session, Review, TutorApplication

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'icon']
    search_fields = ['name', 'category']

@admin.register(Tutor)
class TutorAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'primary_subject', 'year_of_study', 'hourly_rate', 'rating', 'is_verified']
    list_filter = ['year_of_study', 'is_verified']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'bio']

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ['tutor', 'student', 'subject', 'date', 'start_time', 'status']
    list_filter = ['status', 'date']
    search_fields = ['tutor__user__username', 'student__username', 'subject__name']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['tutor', 'student', 'rating', 'is_verified', 'created_at']
    list_filter = ['is_verified', 'created_at']
    search_fields = ['tutor__user__username', 'student__username']

@admin.register(TutorApplication)
class TutorApplicationAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'applied_at', 'reviewed_by']
    list_filter = ['status', 'applied_at']
    search_fields = ['user__username']
