# tutoring/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Tutor, Session, Review
from .forms import TutorRegistrationForm, SessionBookingForm, ReviewForm
from messaging.models import Message, Notification
from accounts.models import CustomUser
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Avg


def tutor_list(request):
    """List all tutors"""
    tutors = Tutor.objects.filter(is_available=True).order_by('-rating')

    # Filter by query parameters
    subject = request.GET.get('subject', '')
    level = request.GET.get('level', '')

    if subject:
        tutors = tutors.filter(primary_subject=subject)
    if level:
        tutors = tutors.filter(year_of_study=level)

    # Calculate average rating safely
    avg_rating = tutors.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0

    stats = {
        'total_tutors': tutors.count(),
        'average_rating': round(avg_rating, 2),
        'total_sessions': Session.objects.count(),
        'subjects_covered': len(Tutor.SUBJECT_CHOICES),
    }

    return render(request, 'tutoring/tutors.html', {
        'tutors': tutors,
        'stats': stats,
    })

def tutor_detail(request, tutor_id):
    """View tutor profile"""
    tutor = get_object_or_404(Tutor, id=tutor_id)
    reviews = Review.objects.filter(tutor=tutor).order_by('-created_at')
    recent_sessions = Session.objects.filter(tutor=tutor).order_by('-date')[:5]

    # Example metrics (replace with real calculation)
    response_rate = 95
    completion_rate = 90
    repeat_rate = 40

    availability_days = [
        {'day': 'Mon', 'time': '4-8 PM', 'available': True},
        {'day': 'Wed', 'time': '4-8 PM', 'available': True},
        {'day': 'Fri', 'time': '2-6 PM', 'available': True},
        {'day': 'Sat', 'time': '10 AM-4 PM', 'available': True},
    ]

    # Convert subjects to a list for template tags
    subjects_list = [s.strip() for s in tutor.subjects.split(',')] if tutor.subjects else []

    context = {
        'tutor': tutor,
        'reviews': reviews,
        'recent_sessions': recent_sessions,
        'availability_days': availability_days,
        'response_rate': response_rate,
        'completion_rate': completion_rate,
        'repeat_rate': repeat_rate,
        'subjects_list': subjects_list,
    }
    return render(request, 'tutoring/tutor_detail.html', context)


@login_required
def become_tutor(request):
    """Tutor registration"""
    if request.method == 'POST':
        form = TutorRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            tutor = form.save(commit=False)
            tutor.user = request.user
            tutor.save()
            messages.success(request, 'Tutor registration successful!')
            return redirect('tutoring:tutor_detail', tutor_id=tutor.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TutorRegistrationForm()
    return render(request, 'tutoring/become_tutor.html', {'form': form})


@login_required
@require_POST
def book_session(request, tutor_id):
    """Book a tutoring session via AJAX"""
    tutor = get_object_or_404(Tutor, id=tutor_id)
    form = SessionBookingForm(request.POST)

    if form.is_valid():
        session = form.save(commit=False)
        session.tutor = tutor
        session.student = request.user
        session.amount = (tutor.hourly_rate / 60) * session.duration
        session.save()
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'error': form.errors.as_json()})


@login_required
@require_POST
def submit_review(request, tutor_id):
    """Submit a review via AJAX"""
    tutor = get_object_or_404(Tutor, id=tutor_id)
    form = ReviewForm(request.POST)

    if form.is_valid():
        review = form.save(commit=False)
        review.tutor = tutor
        review.student = request.user
        review.created_at = timezone.now()
        review.save()
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'error': form.errors.as_json()})


@login_required
@require_POST
def send_to_tutor(request, tutor_id):
    """Send a message to the tutor via AJAX"""
    tutor_user = get_object_or_404(CustomUser, id=tutor_id)
    subject = request.POST.get('subject', '')
    message_body = request.POST.get('message', '')

    if not message_body:
        return JsonResponse({'success': False, 'error': 'Message cannot be empty'})

    Message.objects.create(
        sender=request.user,
        receiver=tutor_user,
        subject=subject,
        body=message_body
    )

    # Optionally, create notification
    Notification.objects.create(
        user=tutor_user,
        title=f"New message from {request.user.username}",
        link=f"/tutoring/tutor/{request.user.id}/"
    )

    return JsonResponse({'success': True})


@login_required
def my_sessions(request):
    """View all sessions of the logged-in user"""
    sessions = Session.objects.filter(student=request.user).order_by('-date')
    return render(request, 'tutoring/my_sessions.html', {'sessions': sessions})


@login_required
def cancel_session(request, session_id):
    """Cancel a session"""
    session = get_object_or_404(Session, id=session_id, student=request.user)

    if request.method == 'POST':
        session.status = 'cancelled'
        session.save()
        messages.success(request, 'Session cancelled successfully!')

    return redirect('tutoring:my_sessions')


@login_required
def update_session_status(request, session_id):
    """Update session status for tutor"""
    session = get_object_or_404(Session, id=session_id, tutor__user=request.user)

    if request.method == 'POST':
        status = request.POST.get('status')
        if status in ['confirmed', 'completed', 'cancelled']:
            session.status = status
            session.save()
            messages.success(request, f'Session marked as {status}')

    return redirect('tutoring:my_sessions')
