# resources/urls.py
from django.urls import path
from . import views

app_name = 'resources'

urlpatterns = [
    path('', views.resource_list, name='list'),
    path('upload/', views.upload_resource, name='upload'),
    path('<int:resource_id>/', views.resource_detail, name='detail'),
    path('<int:resource_id>/update/', views.update_resource, name='update'),
    path('<int:resource_id>/delete/', views.delete_resource, name='delete'),
    path('<int:resource_id>/download/', views.increment_downloads, name='download'),
    path('<int:resource_id>/review/', views.add_resource_review, name='add_review'),
    path('categories/', views.resource_categories, name='categories'),
    path('my-resources/', views.my_resources, name='my_resources'),
]