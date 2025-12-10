# services/urls.py
from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    path('', views.service_directory, name='directory'),
    path('create/', views.create_service, name='create'),
    path('<int:service_id>/', views.service_detail, name='detail'),
    path('<int:service_id>/update/', views.update_service, name='update'),
    path('<int:service_id>/delete/', views.delete_service, name='delete'),
    path('<int:service_id>/review/', views.add_service_review, name='add_review'),
    path('my-services/', views.my_services, name='my_services'),
path('<int:id>/delete/', views.delete_service, name='delete'),
path('<int:id>/update/', views.update_service, name='update'),

    path('category/<str:category>/', views.services_by_category, name='by_category'),
]