from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse, Http404, HttpResponse
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
from django.utils import timezone
import os
from .models import Resource, ResourceReview, ResourceBookmark
from .forms import ResourceForm, ReviewForm
from django.db.models import Sum



def resource_list(request):
    """List all approved resources with advanced filtering"""
    resources = Resource.objects.filter(is_approved=True).order_by('-created_at')

    # Filtering parameters
    resource_type = request.GET.get('type', '')
    subject = request.GET.get('subject', '')
    course_code = request.GET.get('course', '')
    search = request.GET.get('search', '')
    sort = request.GET.get('sort', 'newest')

    # Apply filters
    if resource_type:
        resources = resources.filter(resource_type=resource_type)
    if subject:
        resources = resources.filter(subject=subject)
    if course_code:
        resources = resources.filter(course_code__icontains=course_code)
    if search:
        resources = resources.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(course_code__icontains=search) |
            Q(tags__icontains=search)
        )

    # Apply sorting
    sort_options = {
        'newest': '-created_at',
        'oldest': 'created_at',
        'popular': '-downloads',
        'rating': '-average_rating',
        'title_asc': 'title',
        'title_desc': '-title',
    }
    resources = resources.order_by(sort_options.get(sort, '-created_at'))

    # Get stats for filters
    resource_types = Resource.objects.filter(is_approved=True).values_list(
        'resource_type', flat=True
    ).distinct()

    subjects = Resource.objects.filter(is_approved=True).values_list(
        'subject', flat=True
    ).distinct()

    # Top contributors
    top_contributors = Resource.objects.filter(is_approved=True).values(
        'user__username', 'user__id'
    ).annotate(
        count=Count('id'),
        total_downloads=Sum('downloads')
    ).order_by('-count')[:8]

    # Pagination
    paginator = Paginator(resources, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'resources': page_obj,
        'resource_types': resource_types,
        'subjects': subjects,
        'top_contributors': top_contributors,
        'total_resources': resources.count(),
        'search_query': search,
        'selected_type': resource_type,
        'selected_subject': subject,
        'selected_course': course_code,
        'selected_sort': sort,
    }
    return render(request, 'resources/list.html', context)


def resource_detail(request, pk):
    resource = get_object_or_404(Resource, pk=pk)

    # Hide unapproved resources from non-owners
    if not resource.is_approved and resource.user != request.user:
        raise Http404("Resource not found")

    resource.increment_views()

    reviews = resource.reviews.all().order_by('-created_at')
    review_paginator = Paginator(reviews, 10)
    review_page_obj = review_paginator.get_page(request.GET.get('review_page'))

    user_review = None
    if request.user.is_authenticated:
        user_review = ResourceReview.objects.filter(
            resource=resource, user=request.user
        ).first()

    is_bookmarked = False
    if request.user.is_authenticated:
        is_bookmarked = ResourceBookmark.objects.filter(
            resource=resource, user=request.user
        ).exists()

    related_resources = Resource.objects.filter(
        is_approved=True,
        subject=resource.subject
    ).exclude(pk=resource.pk).order_by('-downloads')[:6]

    user_resources = None
    if request.user.is_authenticated and resource.user == request.user:
        user_resources = Resource.objects.filter(
            user=request.user, is_approved=True
        ).exclude(pk=resource.pk).order_by('-created_at')[:5]

    context = {
        'resource': resource,
        'reviews': review_page_obj,
        'user_review': user_review,
        'is_owner': resource.user == request.user,
        'is_bookmarked': is_bookmarked,
        'related_resources': related_resources,
        'user_resources': user_resources,
        'total_reviews': reviews.count(),
    }

    return render(request, 'resources/detail.html', context)

@login_required
def upload_resource(request):
    """Upload a new resource with improved validation"""
    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.user = request.user

            # Set file size
            if resource.file:
                resource.file_size = resource.file.size

            resource.save()
            messages.success(request, '✅ Resource uploaded successfully! It will be reviewed by moderators.')
            return redirect('resources:detail', pk=resource.pk)
        else:
            messages.error(request, '⚠️ Please correct the errors below.')
    else:
        form = ResourceForm()

    context = {
        'form': form,
        'title': 'Upload Resource',
        'action': 'Upload',
        'btn_text': 'Upload Resource',
        'btn_class': 'btn-success'
    }
    return render(request, 'resources/upload.html', context)


@login_required
def update_resource(request, pk):
    """Update a resource"""
    resource = get_object_or_404(Resource, pk=pk, user=request.user)

    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES, instance=resource)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Resource updated successfully!')
            return redirect('resources:detail', pk=resource.pk)
        else:
            messages.error(request, '⚠️ Please correct the errors below.')
    else:
        form = ResourceForm(instance=resource)

    context = {
        'form': form,
        'resource': resource,
        'title': 'Update Resource',
        'action': 'Update',
        'btn_text': 'Update Resource',
        'btn_class': 'btn-primary'
    }
    return render(request, 'resources/upload.html', context)


@login_required
def delete_resource(request, pk):
    """Delete a resource with confirmation"""
    resource = get_object_or_404(Resource, pk=pk, user=request.user)

    if request.method == 'POST':
        resource.delete()
        messages.success(request, '🗑️ Resource deleted successfully!')
        return redirect('resources:my_resources')

    context = {'resource': resource}
    return render(request, 'resources/confirm_delete.html', context)


def download_resource(request, pk):
    """Download resource file with tracking"""
    resource = get_object_or_404(Resource, pk=pk,)

    # Increment download count
    resource.increment_downloads()

    # Track download if user is authenticated
    if request.user.is_authenticated:
        from .models import ResourceDownload
        ResourceDownload.objects.create(
            resource=resource,
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

    # Serve file
    file_path = resource.file.path
    if os.path.exists(file_path):
        response = FileResponse(open(file_path, 'rb'))
        filename = os.path.basename(file_path)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    else:
        raise Http404("File not found")


@login_required
def add_review(request, pk):
    """Add or update a review for a resource"""
    resource = get_object_or_404(Resource, pk=pk, )

    # Check if user has already reviewed
    existing_review = ResourceReview.objects.filter(
        resource=resource, user=request.user
    ).first()

    if request.method == 'POST':
        if existing_review:
            form = ReviewForm(request.POST, instance=existing_review)
        else:
            form = ReviewForm(request.POST)

        if form.is_valid():
            review = form.save(commit=False)
            review.resource = resource
            review.user = request.user
            review.save()

            # Update resource rating
            resource.update_rating(review.rating)

            messages.success(request, '✅ Review submitted successfully!')
        else:
            messages.error(request, '⚠️ Please correct the errors below.')

    return redirect('resources:detail', pk=resource.pk)


@login_required
def delete_review(request, pk):
    """Delete a review"""
    review = get_object_or_404(ResourceReview, pk=pk, user=request.user)
    resource_pk = review.resource.pk
    review.delete()

    # Recalculate resource rating
    resource = Resource.objects.get(pk=resource_pk)
    reviews = resource.reviews.all()
    if reviews.exists():
        resource.average_rating = reviews.aggregate(Avg('rating'))['rating__avg']
        resource.total_ratings = reviews.count()
    else:
        resource.average_rating = 0.0
        resource.total_ratings = 0
    resource.save()

    messages.success(request, '🗑️ Review deleted successfully!')
    return redirect('resources:detail', pk=resource_pk)


@login_required
def toggle_bookmark(request, pk):
    """Toggle bookmark for a resource"""
    resource = get_object_or_404(Resource, pk=pk)

    bookmark, created = ResourceBookmark.objects.get_or_create(
        resource=resource,
        user=request.user,
        defaults={'created_at': timezone.now()}
    )

    if not created:
        bookmark.delete()
        messages.success(request, '📌 Removed from bookmarks')
    else:
        messages.success(request, '⭐ Added to bookmarks')

    return redirect('resources:detail', pk=resource.pk)


@login_required
def my_resources(request):
    """View user's resources"""
    resources = Resource.objects.filter(user=request.user).order_by('-created_at')

    # Get stats
    total_uploads = resources.count()
    approved_uploads = resources.filter(is_approved=True).count()
    total_downloads = resources.aggregate(Sum('downloads'))['downloads__sum'] or 0
    total_views = resources.aggregate(Sum('views'))['views__sum'] or 0

    context = {
        'resources': resources,
        'stats': {
            'total_uploads': total_uploads,
            'approved_uploads': approved_uploads,
            'total_downloads': total_downloads,
            'total_views': total_views,
        }
    }
    return render(request, 'resources/my_resources.html', context)


@login_required
def my_bookmarks(request):
    """View user's bookmarked resources"""
    bookmarks = ResourceBookmark.objects.filter(
        user=request.user
    ).select_related('resource').order_by('-created_at')

    context = {
        'bookmarks': bookmarks,
        'total_bookmarks': bookmarks.count()
    }
    return render(request, 'resources/my_bookmarks.html', context)


def resource_categories(request):
    """View resource categories with counts"""
    categories = Resource.objects.filter(is_approved=True).values(
        'resource_type', 'subject'
    ).annotate(
        count=Count('id'),
        total_downloads=Sum('downloads')
    ).order_by('-count')

    # Group by resource type
    grouped_categories = {}
    for category in categories:
        resource_type = category['resource_type']
        if resource_type not in grouped_categories:
            grouped_categories[resource_type] = []
        grouped_categories[resource_type].append(category)

    context = {
        'grouped_categories': grouped_categories,
        'total_categories': len(categories)
    }
    return render(request, 'resources/categories.html', context)


def popular_resources(request):
    """View popular resources"""
    resources = Resource.objects.filter(
        is_approved=True
    ).order_by('-downloads')[:20]

    context = {
        'resources': resources,
        'title': 'Most Downloaded Resources'
    }
    return render(request, 'resources/popular.html', context)


def top_rated_resources(request):
    """View top-rated resources"""
    resources = Resource.objects.filter(
        is_approved=True,
        average_rating__gte=3.0,
        total_ratings__gte=3
    ).order_by('-average_rating', '-total_ratings')[:20]

    context = {
        'resources': resources,
        'title': 'Top Rated Resources'
    }
    return render(request, 'resources/popular.html', context)