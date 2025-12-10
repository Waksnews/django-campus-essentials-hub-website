# api/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('recommendations/', views.get_recommendations, name='api_recommendations'),
    path('notifications/', views.get_notifications_api, name='api_notifications'),
    path('notifications/read/', views.mark_notification_read_api, name='api_mark_notification_read'),
    path('leaderboard/', views.get_leaderboard, name='api_leaderboard'),
    path('search/autocomplete/', views.search_autocomplete_api, name='api_search_autocomplete'),
    path('report/', views.report_content, name='api_report'),
]