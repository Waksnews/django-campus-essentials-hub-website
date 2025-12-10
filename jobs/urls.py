# jobs/urls.py
from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    path('', views.job_list, name='list'),
    path('create/', views.create_job, name='create'),
    path('<int:job_id>/', views.job_detail, name='detail'),
    path('<int:job_id>/apply/', views.apply_job, name='apply'),
    path('<int:job_id>/update/', views.update_job, name='update'),
    path('<int:job_id>/delete/', views.delete_job, name='delete'),
    path('<int:job_id>/applications/', views.job_applications, name='applications'),
    path('my-jobs/', views.my_jobs, name='my_jobs'),
    path('applications/<int:app_id>/update/', views.update_application_status, name='update_application'),
    path('applications/<int:app_id>/withdraw/', views.withdraw_application, name='withdraw_application'),
]