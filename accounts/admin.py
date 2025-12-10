# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Badge


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'student_id', 'university',
                    'user_type', 'is_verified', 'points', 'date_joined')
    list_filter = ('user_type', 'is_verified', 'university', 'date_joined')
    search_fields = ('username', 'email', 'student_id', 'university')
    ordering = ('-date_joined',)

    fieldsets = UserAdmin.fieldsets + (
        ('Student Information', {
            'fields': ('student_id', 'university', 'course', 'year_of_study',
                       'phone_number', 'profile_picture', 'bio', 'location')
        }),
        ('Platform Settings', {
            'fields': ('user_type', 'points', 'is_verified',
                       'verification_code', 'dark_mode')
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Student Information', {
            'fields': ('student_id', 'university', 'course', 'year_of_study',
                       'phone_number', 'user_type')
        }),
    )


class BadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge_type', 'awarded_date')
    list_filter = ('badge_type', 'awarded_date')
    search_fields = ('user__username', 'user__email')
    date_hierarchy = 'awarded_date'


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Badge, BadgeAdmin)