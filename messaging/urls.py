# messaging/urls.py
from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('compose/', views.compose_message, name='compose'),
    path('compose/<int:user_id>/', views.compose_to_user, name='compose_to_user'),
    path('thread/<int:user_id>/', views.message_thread, name='thread'),
    path('message/<int:message_id>/', views.message_detail, name='detail'),
    path('message/<int:message_id>/delete/', views.delete_message, name='delete_message'),
    path('notifications/', views.get_notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_read'),
]