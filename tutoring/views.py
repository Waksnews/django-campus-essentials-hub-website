from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST, require_http_methods
from django.utils import timezone
from django.db.models import Q, Avg, Count, Sum
from django.core.paginator import Paginator
from datetime import datetime, date, timedelta
import json

from .models import Tutor, Session, Review, Subject
from .forms import TutorRegistrationForm, SessionBookingForm, ReviewForm, TutorUpdateForm
from messaging.models import Message, Notification
from accounts.models import CustomUser


def tutor_list(request):
    """List all tutors with advanced filtering"""
    tutors = Tutor.objects.filter(is_available=True).select_related('user', 'primary_subject')

    # Filtering
    subject_id = request.GET.get('subject', '')
    level = request.GET.get('level', '')
    min_rate = request.GET.get('min_rate', '')
    max_rate = request.GET.get('max_rate', '')
    search = request.GET.get('search', '')
    sort = request.GET.get('sort', 'rating')

    # Apply filters
    if subject_id:
        tutors = tutors.filter(subjects__id=subject_id)
    if level:
        tutors = tutors.filter(year_of_study=level)
    if min_rate:
        try:
            tutors = tutors.filter(hourly_rate__gte=float(min_rate))
        except ValueError:
            pass
    if max_rate:
        try:
            tutors = tutors.filter(hourly_rate__lte=float(max_rate))
        except ValueError:
            pass
    if search:
        tutors = tutors.filter(
            Q(user__username__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(bio__icontains=search) |
            Q(primary_subject__name__icontains=search)
        )

    # Apply sorting
    sort_options = {
        'rating': '-rating',
        'rate_low': 'hourly_rate',
        'rate_high': '-hourly_rate',
        'experience': '-total_sessions',
        'newest': '-created_at',
        'name_asc': 'user__first_name',
    }
    tutors = tutors.order_by(sort_options.get(sort, '-rating'))

    # Get subjects for filter dropdown
    subjects = Subject.objects.all()

    # Calculate stats
    stats = {
        'total_tutors': tutors.count(),
        'average_rate': tutors.aggregate(avg=Avg('hourly_rate'))['avg'] or 0,
        'top_subject': subjects.annotate(tutor_count=Count('tutors')).order_by('-tutor_count').first(),
        'total_hours': Session.objects.filter(status='completed').aggregate(total=Sum('duration'))['total'] or 0,
    }

    # Pagination
    paginator = Paginator(tutors, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'tutors': page_obj,
        'subjects': subjects,
        'stats': stats,
        'search_query': search,
        'selected_subject': subject_id,
        'selected_level': level,
        'selected_sort': sort,
        'rate_range': {
            'min': 0 if not tutors.exists() else float(min([t.hourly_rate for t in tutors])),
            'max': 0 if not tutors.exists() else float(max([t.hourly_rate for t in tutors])),
        }
    }
    return render(request, 'tutoring/tutors.html', context)


def tutor_detail(request, tutor_id):
    """View tutor profile with booking functionality"""
    tutor = get_object_or_404(Tutor.objects.select_related('user', 'primary_subject'), id=tutor_id)

    # Get reviews with stats
    reviews = Review.objects.filter(tutor=tutor).select_related('student').order_by('-created_at')
    review_paginator = Paginator(reviews, 5)
    review_page = request.GET.get('review_page')
    review_page_obj = review_paginator.get_page(review_page)

    # Calculate review stats - handle missing category fields
    review_stats = {
        'total': reviews.count(),
        'average': reviews.aggregate(avg=Avg('rating'))['avg'] or 0,
    }

    # Safely calculate category ratings
    try:
        review_stats['knowledge'] = reviews.aggregate(avg=Avg('knowledge'))['avg'] or review_stats['average']
        review_stats['teaching'] = reviews.aggregate(avg=Avg('teaching_skill'))['avg'] or review_stats['average']
        review_stats['communication'] = reviews.aggregate(avg=Avg('communication'))['avg'] or review_stats['average']
        review_stats['punctuality'] = reviews.aggregate(avg=Avg('punctuality'))['avg'] or review_stats['average']
    except:
        # If category fields don't exist in database yet
        review_stats['knowledge'] = review_stats['average']
        review_stats['teaching'] = review_stats['average']
        review_stats['communication'] = review_stats['average']
        review_stats['punctuality'] = review_stats['average']

    # Get upcoming sessions (tutor only)
    upcoming_sessions = []
    if request.user.is_authenticated and request.user == tutor.user:
        upcoming_sessions = Session.objects.filter(
            tutor=tutor,
            status__in=['pending', 'confirmed'],
            date__gte=date.today()
        ).select_related('student').order_by('date', 'start_time')[:5]

    # Parse availability from JSON field (CHANGED: using 'availability' not 'availability_slots')
    availability_data = tutor.availability if hasattr(tutor, 'availability') and tutor.availability else {}

    # Create availability display for template
    availability_display = []
    days_mapping = {
        'monday': 'Monday', 'tuesday': 'Tuesday', 'wednesday': 'Wednesday',
        'thursday': 'Thursday', 'friday': 'Friday', 'saturday': 'Saturday',
        'sunday': 'Sunday'
    }

    for day, hours in availability_data.items():
        if hours and isinstance(hours, list):
            day_name = days_mapping.get(day, day.capitalize())
            hours_formatted = ', '.join([f"{h}:00" for h in hours])
            availability_display.append({
                'day': day_name,
                'hours': hours_formatted,
                'available': True
            })

    # If no availability specified, show default message
    if not availability_display:
        availability_display = [{'day': 'Not specified', 'hours': 'Contact for availability', 'available': False}]

    # Check if user has pending booking with this tutor
    has_pending_booking = False
    if request.user.is_authenticated:
        has_pending_booking = Session.objects.filter(
            tutor=tutor,
            student=request.user,
            status='pending'
        ).exists()

    # Check if user has already reviewed this tutor
    user_review = None
    if request.user.is_authenticated:
        user_review = Review.objects.filter(tutor=tutor, student=request.user).first()

    # Check if user is the tutor
    is_owner = request.user.is_authenticated and request.user == tutor.user

    # Get similar tutors - FIXED: use primary_subject instead of subjects
    similar_tutors = []
    if tutor.primary_subject:
        similar_tutors = Tutor.objects.filter(
            is_available=True,
            primary_subject=tutor.primary_subject
        ).exclude(id=tutor.id).order_by('-rating')[:4]

    # Generate next 7 days for availability tab
    next_7_days = []
    for i in range(7):
        day = date.today() + timedelta(days=i)
        day_name = day.strftime('%A').lower()
        # Check if tutor is available on this day
        is_available = day_name in availability_data and availability_data[day_name]
        next_7_days.append({
            'date': day,
            'day_name': day_name,
            'available': bool(is_available)
        })

    context = {
        'tutor': tutor,
        'reviews': review_page_obj,
        'review_stats': review_stats,
        'upcoming_sessions': upcoming_sessions,
        'availability_display': availability_display,  # CHANGED
        'availability_data': availability_data,
        'has_pending_booking': has_pending_booking,
        'user_review': user_review,
        'is_owner': is_owner,
        'similar_tutors': similar_tutors,
        'today': date.today(),
        'next_week': date.today() + timedelta(days=7),
        'next_7_days': next_7_days,  # ADDED
    }
    return render(request, 'tutoring/tutor_detail.html', context)


@login_required
def become_tutor(request):
    """Tutor registration/application"""
    # Check if user is already a tutor
    if hasattr(request.user, 'tutor_profile'):
        messages.info(request, 'You are already registered as a tutor!')
        return redirect('tutoring:tutor_detail', tutor_id=request.user.tutor_profile.id)

    if request.method == 'POST':
        form = TutorRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            tutor = form.save(commit=False)
            tutor.user = request.user

            # Set initial rating and stats
            tutor.rating = 0.0
            tutor.total_sessions = 0
            tutor.total_hours = 0.0
            tutor.is_verified = False  # Admin needs to verify

            tutor.save()
            form.save_m2m()  # Save many-to-many relationships

            messages.success(request,
                             '🎉 Tutor application submitted successfully! '
                             'Your profile will be reviewed by campus staff.'
                             )

            # Create notification for admin
            admin_user = CustomUser.objects.filter(is_superuser=True).first()
            if admin_user:
                Notification.objects.create(
                    user=admin_user,
                    title=f"New Tutor Application: {request.user.username}",
                    message=f"{request.user.username} has applied to become a tutor.",
                    notification_type='tutor_application',
                    link=f"/admin/tutoring/tutor/{tutor.id}/change/"
                )

            return redirect('tutoring:tutor_detail', tutor_id=tutor.id)
        else:
            messages.error(request, '⚠️ Please correct the errors below.')
    else:
        form = TutorRegistrationForm()

    context = {
        'form': form,
        'title': 'Become a Tutor',
        'action': 'Apply Now',
    }
    return render(request, 'tutoring/become_tutor.html', context)


@login_required
def tutor_dashboard(request):
    """Tutor dashboard - manage sessions, availability, etc."""
    if not hasattr(request.user, 'tutor_profile'):
        messages.error(request, 'You are not registered as a tutor.')
        return redirect('tutoring:become_tutor')

    tutor = request.user.tutor_profile

    # Get upcoming sessions
    upcoming_sessions = Session.objects.filter(
        tutor=tutor,
        status__in=['pending', 'confirmed'],
        date__gte=date.today()
    ).select_related('student').order_by('date', 'start_time')

    # Get pending sessions count
    pending_sessions = Session.objects.filter(
        tutor=tutor,
        status='pending',
        date__gte=date.today()
    ).count()

    # Get recent reviews
    recent_reviews = Review.objects.filter(tutor=tutor).select_related('student').order_by('-created_at')[:5]

    # Get earnings for this month
    this_month = timezone.now().month
    this_year = timezone.now().year
    monthly_earnings = Session.objects.filter(
        tutor=tutor,
        status='completed',
        completed_at__month=this_month,
        completed_at__year=this_year,
        payment_status='paid'
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Get total hours taught
    total_hours = tutor.total_hours

    # Generate next 7 days for availability
    next_7_days = []
    availability_data = tutor.availability if hasattr(tutor, 'availability') and tutor.availability else {}
    for i in range(7):
        day = date.today() + timedelta(days=i)
        day_name = day.strftime('%A').lower()
        next_7_days.append({
            'date': day,
            'day_name': day_name,
            'available': day_name in availability_data and availability_data[day_name]
        })

    context = {
        'tutor': tutor,
        'upcoming_sessions': upcoming_sessions,
        'pending_sessions': pending_sessions,
        'recent_reviews': recent_reviews,
        'monthly_earnings': monthly_earnings,
        'total_hours': total_hours,
        'today': date.today(),
        'next_7_days': next_7_days,
        'availability_data': availability_data,
    }
    return render(request, 'tutoring/tutor_dashboard.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def book_session(request, tutor_id):
    """Book a tutoring session"""
    tutor = get_object_or_404(Tutor, id=tutor_id)

    # Check if tutor is available
    if not tutor.is_available:
        messages.error(request, 'This tutor is not currently accepting new sessions.')
        return redirect('tutoring:tutor_detail', tutor_id=tutor_id)

    # Check if user is trying to book themselves
    if request.user == tutor.user:
        messages.error(request, 'You cannot book a session with yourself.')
        return redirect('tutoring:tutor_detail', tutor_id=tutor_id)

    if request.method == 'POST':
        form = SessionBookingForm(request.POST, tutor=tutor, student=request.user)
        if form.is_valid():
            session = form.save(commit=False)
            session.tutor = tutor
            session.student = request.user
            session.amount = (float(tutor.hourly_rate) / 60) * session.duration

            # Check for scheduling conflicts
            conflicting_session = Session.objects.filter(
                tutor=tutor,
                date=session.date,
                start_time__lt=session.end_time,
                end_time__gt=session.start_time,
                status__in=['pending', 'confirmed']
            ).exists()

            if conflicting_session:
                messages.error(request, 'This time slot is already booked. Please choose another time.')
            else:
                session.save()

                # Create notifications
                Notification.objects.create(
                    user=tutor.user,
                    title="New Session Request",
                    message=f"{request.user.username} has requested a session on {session.date}",
                    notification_type='session_request',
                    link=f"/tutoring/sessions/{session.id}/"
                )

                messages.success(request,
                                 '✅ Session request sent successfully! '
                                 'The tutor will confirm the session shortly.'
                                 )
                return redirect('tutoring:my_sessions')
        else:
            messages.error(request, '⚠️ Please correct the errors below.')
    else:
        form = SessionBookingForm(tutor=tutor, student=request.user)

    # Get tutor's availability for the next 2 weeks - CHANGED: using 'availability' not 'availability_slots'
    availability_data = tutor.availability if hasattr(tutor, 'availability') and tutor.availability else {}
    availability = {}
    for i in range(14):
        day = date.today() + timedelta(days=i)
        day_name = day.strftime('%A').lower()
        availability[day] = availability_data.get(day_name, [])

    context = {
        'tutor': tutor,
        'form': form,
        'availability': availability,
        'min_date': date.today(),
        'max_date': date.today() + timedelta(days=13),
    }
    return render(request, 'tutoring/booking.html', context)


@login_required
@require_POST
def submit_review(request, tutor_id):
    """Submit a review for a tutor"""
    tutor = get_object_or_404(Tutor, id=tutor_id)

    # Check if user has completed a session with this tutor
    has_completed_session = Session.objects.filter(
        tutor=tutor,
        student=request.user,
        status='completed'
    ).exists()

    if not has_completed_session:
        return JsonResponse({
            'success': False,
            'error': 'You must complete a session with this tutor before reviewing.'
        }, status=403)

    # Check if user has already reviewed
    existing_review = Review.objects.filter(tutor=tutor, student=request.user).first()

    form = ReviewForm(request.POST, instance=existing_review)
    if form.is_valid():
        review = form.save(commit=False)
        review.tutor = tutor
        review.student = request.user
        review.save()

        # Update tutor rating
        tutor.update_rating()

        return JsonResponse({
            'success': True,
            'message': 'Review submitted successfully!',
            'review_id': review.id
        })
    else:
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)


@login_required
@require_POST
def send_to_tutor(request, tutor_id):
    """Send a message to the tutor"""
    tutor = get_object_or_404(Tutor, id=tutor_id)
    tutor_user = tutor.user

    if request.user == tutor_user:
        return JsonResponse({
            'success': False,
            'error': 'You cannot message yourself.'
        }, status=400)

    subject = request.POST.get('subject', 'Inquiry about tutoring')
    message_body = request.POST.get('message', '')

    if not message_body.strip():
        return JsonResponse({
            'success': False,
            'error': 'Message cannot be empty.'
        }, status=400)

    # Create message
    Message.objects.create(
        sender=request.user,
        receiver=tutor_user,
        subject=subject,
        body=message_body,
        message_type='tutoring_inquiry'
    )

    # Create notification
    Notification.objects.create(
        user=tutor_user,
        title=f"New message from {request.user.username}",
        message=message_body[:100] + ('...' if len(message_body) > 100 else ''),
        notification_type='message',
        link=f"/messaging/inbox/"
    )

    return JsonResponse({
        'success': True,
        'message': 'Message sent successfully!'
    })


@login_required
def my_sessions(request):
    """View user's sessions (both as student and tutor)"""
    # Sessions as student
    student_sessions = Session.objects.filter(
        student=request.user
    ).select_related('tutor', 'tutor__user').order_by('-date', '-start_time')

    # Sessions as tutor (if user is a tutor)
    tutor_sessions = None
    if hasattr(request.user, 'tutor_profile'):
        tutor_sessions = Session.objects.filter(
            tutor=request.user.tutor_profile
        ).select_related('student').order_by('-date', '-start_time')

    # Separate by status
    upcoming_student = student_sessions.filter(
        status__in=['pending', 'confirmed'],
        date__gte=date.today()
    )
    past_student = student_sessions.filter(
        Q(status='completed') |
        Q(date__lt=date.today())
    )

    upcoming_tutor = tutor_sessions.filter(
        status__in=['pending', 'confirmed'],
        date__gte=date.today()
    ) if tutor_sessions else []
    past_tutor = tutor_sessions.filter(
        Q(status='completed') |
        Q(date__lt=date.today())
    ) if tutor_sessions else []

    # Calculate totals
    total_spent = sum(session.amount for session in past_student if session.status == 'completed')
    pending_sessions_count = upcoming_student.filter(status='pending').count()

    context = {
        'upcoming_student': upcoming_student,
        'past_student': past_student,
        'upcoming_tutor': upcoming_tutor,
        'past_tutor': past_tutor,
        'is_tutor': hasattr(request.user, 'tutor_profile'),
        'today': date.today(),
        'total_spent': total_spent,
        'pending_sessions_count': pending_sessions_count,
    }
    return render(request, 'tutoring/my_sessions.html', context)


@login_required
@require_http_methods(["POST"])
def cancel_session(request, session_id):
    """Cancel a session (student or tutor)"""
    session = get_object_or_404(Session, id=session_id)

    # Check permission
    if request.user != session.student and request.user != session.tutor.user:
        return HttpResponseForbidden("You don't have permission to cancel this session.")

    # Check if cancellation is allowed (at least 24 hours before)
    session_datetime = datetime.combine(session.date, session.start_time)
    if timezone.now() + timedelta(hours=24) > session_datetime:
        messages.error(request, 'Sessions can only be cancelled at least 24 hours in advance.')
        return redirect('tutoring:my_sessions')

    # Update session
    session.status = 'cancelled'
    session.cancelled_at = timezone.now()
    session.save()

    # Create notification for the other party
    other_user = session.tutor.user if request.user == session.student else session.student
    Notification.objects.create(
        user=other_user,
        title="Session Cancelled",
        message=f"Session on {session.date} has been cancelled.",
        notification_type='session_update',
        link=f"/tutoring/sessions/{session.id}/"
    )

    messages.success(request, 'Session cancelled successfully.')
    return redirect('tutoring:my_sessions')


@login_required
@require_POST
def update_session_status(request, session_id):
    """Update session status (tutor only)"""
    session = get_object_or_404(Session, id=session_id)

    # Check if user is the tutor
    if not hasattr(request.user, 'tutor_profile') or request.user.tutor_profile != session.tutor:
        return HttpResponseForbidden("Only the tutor can update session status.")

    status = request.POST.get('status')
    if status not in ['confirmed', 'completed', 'cancelled']:
        messages.error(request, 'Invalid status.')
        return redirect('tutoring:my_sessions')

    # Update session
    old_status = session.status
    session.status = status

    if status == 'confirmed' and old_status != 'confirmed':
        session.confirmed_at = timezone.now()
    elif status == 'completed' and old_status != 'completed':
        session.completed_at = timezone.now()
    elif status == 'cancelled' and old_status != 'cancelled':
        session.cancelled_at = timezone.now()

    session.save()

    # Create notification for student
    Notification.objects.create(
        user=session.student,
        title=f"Session {status.capitalize()}",
        message=f"Your session on {session.date} has been marked as {status}.",
        notification_type='session_update',
        link=f"/tutoring/sessions/{session.id}/"
    )

    messages.success(request, f'Session marked as {status}.')
    return redirect('tutoring:my_sessions')


@login_required
def session_detail(request, session_id):
    """View session details"""
    session = get_object_or_404(Session.objects.select_related(
        'tutor', 'tutor__user', 'student', 'subject'
    ), id=session_id)

    # Check permission
    if request.user != session.student and request.user != session.tutor.user:
        return HttpResponseForbidden("You don't have permission to view this session.")

    # Check if review exists
    has_review = hasattr(session, 'session_review')

    context = {
        'session': session,
        'is_student': request.user == session.student,
        'is_tutor': request.user == session.tutor.user,
        'can_review': (request.user == session.student and
                       session.status == 'completed' and
                       not has_review),
    }
    return render(request, 'tutoring/session_detail.html', context)


@login_required
def update_availability(request):
    """Update tutor availability"""
    if not hasattr(request.user, 'tutor_profile'):
        messages.error(request, 'You are not registered as a tutor.')
        return redirect('tutoring:become_tutor')

    tutor = request.user.tutor_profile

    if request.method == 'POST':
        # Handle availability update via AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                data = json.loads(request.body)
                # CHANGED: using 'availability' not 'availability_slots'
                tutor.availability = data.get('slots', {})
                tutor.save()
                return JsonResponse({'success': True})
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'error': 'Invalid JSON'})

    # GET request - render form
    availability_data = tutor.availability if hasattr(tutor, 'availability') and tutor.availability else {}

    context = {
        'tutor': tutor,
        'days': [
            {'id': 'monday', 'name': 'Monday'},
            {'id': 'tuesday', 'name': 'Tuesday'},
            {'id': 'wednesday', 'name': 'Wednesday'},
            {'id': 'thursday', 'name': 'Thursday'},
            {'id': 'friday', 'name': 'Friday'},
            {'id': 'saturday', 'name': 'Saturday'},
            {'id': 'sunday', 'name': 'Sunday'},
        ],
        'time_slots': list(range(8, 22)),  # 8 AM to 10 PM
        'availability_data': availability_data,
    }
    return render(request, 'tutoring/update_availability.html', context)