# accounts/views.py
import random
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .forms import CustomUserCreationForm, ProfileUpdateForm
from .models import CustomUser, Badge
from lost_found.models import LostItem
from tutoring.models import Session
from jobs.models import Job
from resources.models import Resource
import json


def register(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Send verification email (simplified)
            messages.success(request,
                             'Registration successful! Please check your email for verification.')

            # Auto-login after registration
            login(request, user)
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/register.html', {'form': form})


def user_login(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'accounts/login.html')


def user_logout(request):
    """User logout view"""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


@login_required
def dashboard(request):
    """User dashboard view"""
    user = request.user

    # Get user stats
    stats = {
        'my_items': LostItem.objects.filter(user=user).count(),
        'my_sessions': Session.objects.filter(student=user).count(),
        'my_jobs': Job.objects.filter(user=user).count(),
        'my_resources': Resource.objects.filter(user=user).count(),
    }

    # Get recent activity
    recent_activity = []

    # Lost items activity
    for item in LostItem.objects.filter(user=user).order_by('-created_at')[:3]:
        recent_activity.append({
            'icon': 'search',
            'color': 'primary',
            'message': f'You reported a lost item: {item.title}',
            'timestamp': item.created_at,
            'link': f'/lost-found/{item.id}/'
        })

    # Tutoring activity
    for session in Session.objects.filter(student=user).order_by('-created_at')[:2]:
        recent_activity.append({
            'icon': 'chalkboard-teacher',
            'color': 'success',
            'message': f'You booked a session with {session.tutor.user.username}',
            'timestamp': session.created_at,
            'link': f'/tutoring/session/{session.id}/'
        })

    # Sort by timestamp
    recent_activity.sort(key=lambda x: x['timestamp'], reverse=True)

    # Get user badges
    badges = user.badges.all()[:4]

    # Generate recommendations
    recommendations = []
    if user.course:
        recommendations.append({
            'title': f'Tutors for {user.course}',
            'description': 'Find expert tutors in your course',
            'type': 'success',
            'link': '/tutoring/'
        })

    # Prepare chart data
    chart_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
    chart_items_data = [random.randint(0, 10) for _ in range(6)]
    chart_services_data = [random.randint(0, 15) for _ in range(6)]
    chart_jobs_data = [random.randint(0, 8) for _ in range(6)]

    context = {
        'stats': stats,
        'recent_activity': recent_activity[:5],
        'badges': badges,
        'recommendations': recommendations,
        'chart_labels': json.dumps(chart_labels),
        'chart_items_data': json.dumps(chart_items_data),
        'chart_services_data': json.dumps(chart_services_data),
        'chart_jobs_data': json.dumps(chart_jobs_data),
    }

    return render(request, 'accounts/dashboard.html', context)


@login_required
def profile(request):
    """User profile view"""
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(request, 'accounts/profile.html', {'form': form})


def theme_toggle(request):
    """Toggle theme preference"""
    if request.method == 'POST' and request.user.is_authenticated:
        data = json.loads(request.body)
        theme = data.get('theme')

        if theme in ['light', 'dark']:
            request.user.dark_mode = (theme == 'dark')
            request.user.save()
            return JsonResponse({'success': True})

    return JsonResponse({'success': False})