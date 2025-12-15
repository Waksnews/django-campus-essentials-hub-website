# ceh_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import home, about, announcements, contact
from accounts.views import theme_toggle

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('about/', about, name='about'),
    path('announcements/', announcements, name='announcements'),
    path('contact/', contact, name='contact'),

    # Accounts
    path('accounts/', include('accounts.urls')),

    # Apps
    path('lost-found/', include('lost_found.urls')),
    path('tutoring/', include('tutoring.urls')),
    path('jobs/', include('jobs.urls')),
    path('resources/', include('resources.urls')),
    path('services/', include('services.urls')),
    path('messaging/', include('messaging.urls')),
    # API endpoints
    path('api/', include('api.urls')),
    path('api/theme-toggle/', theme_toggle, name='theme_toggle'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)