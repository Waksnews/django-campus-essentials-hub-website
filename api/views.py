# api/views.py
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
import json
from core.recommendations import RecommendationEngine
from accounts.gamification import GamificationEngine
from messaging.models import Notification


@login_required
@require_GET
def get_recommendations(request):
    """Get personalized recommendations"""
    engine = RecommendationEngine(request.user)
    recommendations = engine.get_recommendations(limit=5)
    return JsonResponse({'recommendations': recommendations})


@login_required
@require_GET
def get_notifications_api(request):
    """Get unread notifications"""
    notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).order_by('-created_at')[:10]

    data = [{
        'id': n.id,
        'type': n.notification_type,
        'title': n.title,
        'message': n.message,
        'link': n.link,
        'time': n.created_at.strftime('%I:%M %p'),
        'is_read': n.is_read,
    } for n in notifications]

    return JsonResponse({'notifications': data})


@login_required
@require_POST
def mark_notification_read_api(request):
    """Mark notification as read"""
    data = json.loads(request.body)
    notification_id = data.get('notification_id')

    try:
        notification = Notification.objects.get(
            id=notification_id,
            user=request.user
        )
        notification.is_read = True
        notification.save()
        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notification not found'})


@login_required
@require_GET
def get_leaderboard(request):
    """Get leaderboard data"""
    gamification = GamificationEngine(request.user)
    leaderboard = gamification.get_leaderboard(limit=20)

    data = []
    for rank, user in enumerate(leaderboard, start=1):
        data.append({
            'rank': rank,
            'username': user.username,
            'points': user.points,
            'badges_count': user.badges.count(),
            'is_current_user': user == request.user
        })

    return JsonResponse({'leaderboard': data})


@login_required
@require_GET
def search_autocomplete_api(request):
    """Search autocomplete endpoint"""
    query = request.GET.get('q', '')
    results = []

    if len(query) >= 2:
        from lost_found.models import LostItem
        from tutoring.models import Tutor
        from jobs.models import Job
        from resources.models import Resource
        from services.models import Service

        # Search lost items
        lost_items = LostItem.objects.filter(
            title__icontains=query
        )[:3]
        results.extend([{
            'type': 'lost_item',
            'title': item.title,
            'description': f"Lost {item.get_category_display()}",
            'link': f'/lost-found/{item.id}/'
        } for item in lost_items])

        # Search tutors
        tutors = Tutor.objects.filter(
            user__username__icontains=query
        )[:3]
        results.extend([{
            'type': 'tutor',
            'title': tutor.user.username,
            'description': f"{tutor.get_primary_subject_display()} Tutor",
            'link': f'/tutoring/{tutor.id}/'
        } for tutor in tutors])

        # Search jobs
        jobs = Job.objects.filter(
            title__icontains=query
        )[:3]
        results.extend([{
            'type': 'job',
            'title': job.title,
            'description': job.get_category_display(),
            'link': f'/jobs/{job.id}/'
        } for job in jobs])

    return JsonResponse({'results': results[:10]})


@csrf_exempt
@require_POST
def report_content(request):
    """Report inappropriate content"""
    try:
        data = json.loads(request.body)
        content_type = data.get('content_type')
        content_id = data.get('content_id')
        reason = data.get('reason')
        description = data.get('description')

        # Create report entry
        from core.models import ContentReport
        report = ContentReport.objects.create(
            reporter=request.user if request.user.is_authenticated else None,
            content_type=content_type,
            content_id=content_id,
            reason=reason,
            description=description,
            ip_address=request.META.get('REMOTE_ADDR')
        )

        # Notify admin
        from django.contrib.auth.models import User
        admin_users = User.objects.filter(is_staff=True)
        for admin in admin_users:
            Notification.objects.create(
                user=admin,
                notification_type='system',
                title='Content Reported',
                message=f'New content report: {reason}',
                link=f'/admin/core/contentreport/{report.id}/'
            )

        return JsonResponse({'success': True, 'report_id': report.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})