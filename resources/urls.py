from django.urls import path
from . import views

app_name = 'resources'

urlpatterns = [
    # List views
    path('', views.resource_list, name='list'),
    path('categories/', views.resource_categories, name='categories'),
    path('popular/', views.popular_resources, name='popular'),
    path('top-rated/', views.top_rated_resources, name='top_rated'),

    # User-specific views
    path('my-resources/', views.my_resources, name='my_resources'),
    path('my-bookmarks/', views.my_bookmarks, name='my_bookmarks'),

    # Resource CRUD operations
    path('upload/', views.upload_resource, name='upload'),
    path('<int:pk>/', views.resource_detail, name='detail'),
    path('<int:pk>/update/', views.update_resource, name='update'),
    path('<int:pk>/delete/', views.delete_resource, name='delete'),
    path('<int:pk>/download/', views.download_resource, name='download'),

    # Reviews
    path('<int:pk>/review/', views.add_review, name='add_review'),
    path('review/<int:pk>/delete/', views.delete_review, name='delete_review'),

    # Bookmarks
    path('<int:pk>/bookmark/', views.toggle_bookmark, name='toggle_bookmark'),
]