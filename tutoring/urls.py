# tutoring/urls.py
from django.urls import path
from . import views

app_name = 'tutoring'

urlpatterns = [
    # Tutor listing
    path('', views.tutor_list, name='tutors'),

    # Become a tutor
    path('become-tutor/', views.become_tutor, name='become_tutor'),

    # Tutor profile/detail
    path('<int:tutor_id>/', views.tutor_detail, name='tutor_detail'),

    # Messaging tutor
    path('<int:tutor_id>/message/', views.send_to_tutor, name='send_to_tutor'),

    # Book a session (AJAX)
    path('<int:tutor_id>/book/', views.book_session, name='book_session'),

    # Submit a review (AJAX)
    path('<int:tutor_id>/review/', views.submit_review, name='submit_review'),

    # Student's sessions
    path('sessions/', views.my_sessions, name='my_sessions'),

    # Cancel a session
    path('sessions/<int:session_id>/cancel/', views.cancel_session, name='cancel_session'),

    # Update session status (for tutors)
    path('sessions/<int:session_id>/update/', views.update_session_status, name='update_session_status'),
]
