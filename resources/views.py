# resources/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from .models import Resource, ResourceReview
from .forms import ResourceForm, ReviewForm
from django.db.models import Count



def resource_list(request):
    """List all resources"""
    resources = Resource.objects.filter(is_approved=True).order_by('-created_at')

    # Filtering
    resource_type = request.GET.get('type', '')
    subject = request.GET.get('subject', '')

    if resource_type:
        resources = resources.filter(resource_type=resource_type)
    if subject:
        resources = resources.filter(subject=subject)

    return render(request, 'resources/list.html', {
        'resources': resources,
        'top_contributors': Resource.objects.values('user__username').annotate(
            count=Count('id')
        ).order_by('-count')[:6],
    })


def resource_detail(request, resource_id):
    """View resource details"""
    resource = get_object_or_404(Resource, id=resource_id)
    reviews = ResourceReview.objects.filter(resource=resource).order_by('-created_at')

    return render(request, 'resources/detail.html', {
        'resource': resource,
        'reviews': reviews,
        'is_owner': resource.user == request.user,
    })


@login_required
def upload_resource(request):
    """Upload a new resource"""
    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.user = request.user
            resource.save()
            messages.success(request, 'Resource uploaded successfully!')
            return redirect('resources:detail', resource_id=resource.id)
    else:
        form = ResourceForm()

    return render(request, 'resources/upload.html', {'form': form})


@login_required
def update_resource(request, resource_id):
    """Update a resource"""
    resource = get_object_or_404(Resource, id=resource_id, user=request.user)

    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES, instance=resource)
        if form.is_valid():
            form.save()
            messages.success(request, 'Resource updated successfully!')
            return redirect('resources:detail', resource_id=resource.id)
    else:
        form = ResourceForm(instance=resource)

    return render(request, 'resources/update.html', {'form': form, 'resource': resource})


@login_required
def delete_resource(request, resource_id):
    """Delete a resource"""
    resource = get_object_or_404(Resource, id=resource_id, user=request.user)

    if request.method == 'POST':
        resource.delete()
        messages.success(request, 'Resource deleted successfully!')
        return redirect('resources:list')

    return render(request, 'resources/confirm_delete.html', {'resource': resource})


def increment_downloads(request, resource_id):
    """Increment download count"""
    resource = get_object_or_404(Resource, id=resource_id)
    resource.downloads += 1
    resource.save()

    response = HttpResponse(resource.file.read(), content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{resource.file.name}"'
    return response


@login_required
def add_resource_review(request, resource_id):
    """Add a review to a resource"""
    resource = get_object_or_404(Resource, id=resource_id)

    # Check if already reviewed
    if ResourceReview.objects.filter(resource=resource, user=request.user).exists():
        messages.warning(request, 'You have already reviewed this resource.')
        return redirect('resources:detail', resource_id=resource.id)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.resource = resource
            review.user = request.user
            review.save()
            messages.success(request, 'Review added successfully!')

    return redirect('resources:detail', resource_id=resource.id)


def resource_categories(request):
    """View resource categories"""
    categories = Resource.objects.values('resource_type').annotate(
        count=Count('id')
    )
    return render(request, 'resources/categories.html', {'categories': categories})


@login_required
def my_resources(request):
    """View user's resources"""
    resources = Resource.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'resources/my_resources.html', {'resources': resources})