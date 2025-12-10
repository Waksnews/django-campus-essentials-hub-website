# core/context_processors.py
from messaging.models import Notification

def notification_count(request):
    """Add notification count to all templates"""
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        return {'notification_count': unread_count}
    return {'notification_count': 0}

def theme_preference(request):
    """Add theme preference to all templates"""
    if request.user.is_authenticated:
        theme = 'dark' if request.user.dark_mode else 'light'
        return {'theme': theme}
    return {'theme': 'light'}