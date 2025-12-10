# core/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from accounts.models import CustomUser
from lost_found.models import LostItem
from tutoring.models import Tutor
from jobs.models import Job
from resources.models import Resource
import random


def home(request):
    """Home page view"""
    # Get stats for display
    stats = {
        'total_users': CustomUser.objects.count(),
        'active_tutors': Tutor.objects.filter(is_available=True).count(),
        'jobs_posted': Job.objects.filter(status='open').count(),
        'resources_shared': Resource.objects.filter(is_approved=True).count(),
        'items_found': LostItem.objects.filter(status='found').count(),
    }

    # Get featured items
    featured_tutors = Tutor.objects.filter(is_available=True).order_by('-rating')[:3]
    featured_jobs = Job.objects.filter(status='open').order_by('-created_at')[:3]
    recent_items = LostItem.objects.filter(status='lost').order_by('-created_at')[:5]

    context = {
        'stats': stats,
        'featured_tutors': featured_tutors,
        'featured_jobs': featured_jobs,
        'recent_items': recent_items,
    }
    return render(request, 'core/home.html', context)


def about(request):
    """About page view"""
    return render(request, 'core/about.html')


def announcements(request):
    """Announcements page view"""
    announcements_list = [
        {
            'title': 'Mid-Semester Exams Schedule',
            'content': 'The mid-semester exams schedule has been released. Check your department notice board.',
            'date': '2024-03-15',
            'category': 'Academic'
        },
        {
            'title': 'Career Fair 2024',
            'content': 'Annual career fair on April 10th. Register at the careers office.',
            'date': '2024-03-10',
            'category': 'Events'
        },
        {
            'title': 'System Maintenance',
            'content': 'Platform will be under maintenance on March 20th from 2 AM to 4 AM.',
            'date': '2024-03-05',
            'category': 'System'
        },
    ]
    return render(request, 'core/announcements.html', {'announcements': announcements_list})


def contact(request):
    """Contact page view"""
    if request.method == 'POST':
        # Handle contact form submission
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        # Here you would typically send an email
        messages.success(request, 'Thank you for your message. We will get back to you soon!')
        return redirect('contact')

    return render(request, 'core/contact.html')


# Context processors
def notification_count(request):
    """Add notification count to all templates"""
    if request.user.is_authenticated:
        from messaging.models import Notification
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        return {'notification_count': unread_count}
    return {'notification_count': 0}


def theme_preference(request):
    """Add theme preference to all templates"""
    if request.user.is_authenticated:
        theme = 'dark' if request.user.dark_mode else 'light'
        return {'theme': theme}
    return {'theme': 'light'}