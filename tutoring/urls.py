from django.urls import path
from . import views

app_name = 'tutoring'

urlpatterns = [
    # Public views
    path('', views.tutor_list, name='tutors'),
    path('tutor/<int:tutor_id>/', views.tutor_detail, name='tutor_detail'),

    # Tutor registration
    path('become-tutor/', views.become_tutor, name='become_tutor'),
    path('dashboard/', views.tutor_dashboard, name='tutor_dashboard'),
    path('availability/', views.update_availability, name='update_availability'),

    # Session booking
    path('tutor/<int:tutor_id>/book/', views.book_session, name='book_session'),
    path('sessions/<int:session_id>/', views.session_detail, name='session_detail'),

    # Reviews
    path('tutor/<int:tutor_id>/review/', views.submit_review, name='submit_review'),

    # Messaging
    path('tutor/<int:tutor_id>/message/', views.send_to_tutor, name='send_to_tutor'),

    # User sessions
    path('my-sessions/', views.my_sessions, name='my_sessions'),
    path('sessions/<int:session_id>/cancel/', views.cancel_session, name='cancel_session'),
    path('sessions/<int:session_id>/update/', views.update_session_status, name='update_session_status'),
]