# messaging/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Message, Notification
from accounts.models import CustomUser
import json
from django.db.models import Q



@login_required
def inbox(request):
    """View all messages"""
    messages = Message.objects.filter(
        receiver=request.user
    ).order_by('-sent_at')

    unread_count = messages.filter(is_read=False).count()

    return render(request, 'messaging/inbox.html', {
        'messages': messages,
        'unread_count': unread_count,
    })


@login_required
def message_thread(request, user_id):
    """View conversation thread with a user"""
    other_user = get_object_or_404(CustomUser, id=user_id)

    # Get messages between users
    messages = Message.objects.filter(
        (Q(sender=request.user) & Q(receiver=other_user)) |
        (Q(sender=other_user) & Q(receiver=request.user))
    ).order_by('sent_at')

    # Mark as read
    messages.filter(receiver=request.user, is_read=False).update(is_read=True)

    return render(request, 'messaging/thread.html', {
        'other_user': other_user,
        'messages': messages,
    })


@login_required
def compose_message(request):
    """Compose a new message"""
    if request.method == 'POST':
        receiver_id = request.POST.get('receiver_id')
        subject = request.POST.get('subject')
        body = request.POST.get('body')

        try:
            receiver = CustomUser.objects.get(id=receiver_id)
            message = Message.objects.create(
                sender=request.user,
                receiver=receiver,
                subject=subject,
                body=body
            )
            messages.success(request, 'Message sent successfully!')
            return redirect('messaging:thread', user_id=receiver_id)
        except CustomUser.DoesNotExist:
            messages.error(request, 'User not found.')

    return render(request, 'messaging/compose.html')


@login_required
def compose_to_user(request, user_id):
    """Compose message to specific user"""
    receiver = get_object_or_404(CustomUser, id=user_id)
    return render(request, 'messaging/compose.html', {'receiver': receiver})


@login_required
def message_detail(request, message_id):
    """View message details"""
    message = get_object_or_404(Message, id=message_id, receiver=request.user)

    # Mark as read
    if not message.is_read:
        message.is_read = True
        message.save()

    return render(request, 'messaging/detail.html', {'message': message})


@login_required
def delete_message(request, message_id):
    """Delete a message"""
    message = get_object_or_404(Message, id=message_id, receiver=request.user)

    if request.method == 'POST':
        message.delete()
        messages.success(request, 'Message deleted successfully!')
        return redirect('messaging:inbox')

    return render(request, 'messaging/confirm_delete.html', {'message': message})


@login_required
def get_notifications(request):
    """Get unread notifications (API endpoint)"""
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
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'success': True})


@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})