# services/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Service, ServiceReview
from .forms import ServiceForm, ServiceReviewForm


def service_directory(request):
    """List all services"""
    services = Service.objects.all().order_by('-created_at')

    # Filtering
    category = request.GET.get('category', '')
    location = request.GET.get('location', '')

    if category:
        services = services.filter(category=category)
    if location:
        services = services.filter(location__icontains=location)

    return render(request, 'services/directory.html', {'services': services})


def service_detail(request, service_id):
    """View service details"""
    service = get_object_or_404(Service, id=service_id)
    reviews = ServiceReview.objects.filter(service=service).order_by('-created_at')

    return render(request, 'services/detail.html', {
        'service': service,
        'reviews': reviews,
        'is_owner': service.user == request.user,
    })


@login_required
def create_service(request):
    """Create a new service"""
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.user = request.user
            service.save()
            messages.success(request, 'Service added successfully!')
            return redirect('services:detail', service_id=service.id)
    else:
        form = ServiceForm()

    return render(request, 'services/create.html', {'form': form})


@login_required
def update_service(request, service_id):
    """Update a service"""
    service = get_object_or_404(Service, id=service_id, user=request.user)

    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, 'Service updated successfully!')
            return redirect('services:detail', service_id=service.id)
    else:
        form = ServiceForm(instance=service)

    return render(request, 'services/update.html', {'form': form, 'service': service})


@login_required
def delete_service(request, service_id):
    """Delete a service"""
    service = get_object_or_404(Service, id=service_id, user=request.user)

    if request.method == 'POST':
        service.delete()
        messages.success(request, 'Service deleted successfully!')
        return redirect('services:directory')

    return render(request, 'services/confirm_delete.html', {'service': service})


@login_required
def add_service_review(request, service_id):
    """Add a review to a service"""
    service = get_object_or_404(Service, id=service_id)

    if request.method == 'POST':
        form = ServiceReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.service = service
            review.user = request.user
            review.save()
            messages.success(request, 'Review added successfully!')

    return redirect('services:detail', service_id=service.id)

@login_required
def delete_service(request, id):
    service = get_object_or_404(Service, id=id)

    if request.method == 'POST':
        service.delete()
        return redirect('services:directory')

    return HttpResponseNotAllowed(['POST'])

@login_required
def my_services(request):
    """View user's services"""
    services = Service.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'services/my_services.html', {'services': services})


def services_by_category(request, category):
    """View services by category"""
    services = Service.objects.filter(category=category).order_by('-created_at')
    return render(request, 'services/directory.html', {
        'services': services,
        'category': category,
    })