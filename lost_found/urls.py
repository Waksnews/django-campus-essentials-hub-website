# lost_found/urls.py
from django.urls import path
from . import views

app_name = 'lost_found'

urlpatterns = [
    path('', views.item_list, name='list'),
    path('create/lost/', views.create_lost_item, name='create_lost'),
    path('create/found/', views.create_found_item, name='create_found'),
    path('<int:item_id>/', views.item_detail, name='detail'),
    path('<int:item_id>/resolve/', views.mark_as_resolved, name='resolve'),
    path('<int:item_id>/update/', views.update_item, name='update'),
    path('<int:item_id>/delete/', views.delete_item, name='delete'),
    path('search/autocomplete/', views.search_autocomplete, name='autocomplete'),
    path('my-items/', views.my_items, name='my_items'),
    path('category/<str:category>/', views.items_by_category, name='by_category'),
]