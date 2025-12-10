# lost_found/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from .models import LostItem, FoundItem
from .forms import LostItemForm, FoundItemForm, SearchForm


def item_list(request):
    """List all lost and found items"""
    form = SearchForm(request.GET or None)
    items = LostItem.objects.all().order_by('-created_at')

    if form.is_valid():
        query = form.cleaned_data.get('query')
        category = form.cleaned_data.get('category')
        status = form.cleaned_data.get('status')
        date_range = form.cleaned_data.get('date_range')

        if query:
            items = items.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(location_lost__icontains=query)
            )

        if category:
            items = items.filter(category=category)

        if status:
            items = items.filter(status=status)

    context = {
        'items': items,
        'form': form,
        'total_items': items.count(),
        'found_items': items.filter(status='found').count(),
        'lost_items': items.filter(status='lost').count(),
    }
    return render(request, 'lost_found/list.html', context)


@login_required
def create_lost_item(request):
    """Create a new lost item report"""
    if request.method == 'POST':
        form = LostItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            item.save()
            messages.success(request, 'Lost item reported successfully!')
            return redirect('lost_found:detail', item_id=item.id)
    else:
        form = LostItemForm()

    return render(request, 'lost_found/create.html', {'form': form, 'type': 'lost'})


@login_required
def create_found_item(request):
    """Create a new found item report"""
    if request.method == 'POST':
        form = FoundItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            item.save()
            messages.success(request, 'Found item reported successfully!')
            return redirect('lost_found:detail', item_id=item.id)
    else:
        form = FoundItemForm()

    return render(request, 'lost_found/create.html', {'form': form, 'type': 'found'})


def item_detail(request, item_id):
    """View item details"""
    item = get_object_or_404(LostItem, id=item_id)

    # Find potential matches
    potential_matches = []
    if item.status == 'lost':
        potential_matches = FoundItem.objects.filter(
            category=item.category,
            is_claimed=False
        ).exclude(user=item.user)[:3]

    context = {
        'item': item,
        'potential_matches': potential_matches,
        'is_owner': request.user == item.user,
    }
    return render(request, 'lost_found/detail.html', context)


@login_required
def update_item(request, item_id):
    """Update an item"""
    item = get_object_or_404(LostItem, id=item_id, user=request.user)

    if request.method == 'POST':
        form = LostItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Item updated successfully!')
            return redirect('lost_found:detail', item_id=item.id)
    else:
        form = LostItemForm(instance=item)

    return render(request, 'lost_found/update.html', {'form': form, 'item': item})


@login_required
def delete_item(request, item_id):
    """Delete an item"""
    item = get_object_or_404(LostItem, id=item_id, user=request.user)

    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Item deleted successfully!')
        return redirect('lost_found:list')

    return render(request, 'lost_found/confirm_delete.html', {'item': item})


@login_required
def mark_as_resolved(request, item_id):
    """Mark item as resolved/claimed"""
    item = get_object_or_404(LostItem, id=item_id)

    if request.user == item.user or request.user.is_staff:
        item.is_resolved = True
        if item.status == 'lost':
            item.status = 'returned'
        else:
            item.status = 'claimed'
        item.save()
        messages.success(request, 'Item marked as resolved!')

    return redirect('lost_found:detail', item_id=item_id)


def search_autocomplete(request):
    """Autocomplete search for lost and found items"""
    query = request.GET.get('q', '')
    if query:
        items = LostItem.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )[:10]

        results = [{'id': item.id, 'title': item.title} for item in items]
        return JsonResponse({'results': results})

    return JsonResponse({'results': []})


@login_required
def my_items(request):
    """View user's items"""
    items = LostItem.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'lost_found/my_items.html', {'items': items})


def items_by_category(request, category):
    """View items by category"""
    items = LostItem.objects.filter(category=category).order_by('-created_at')
    return render(request, 'lost_found/list.html', {
        'items': items,
        'category': category,
    })