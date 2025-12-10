# lost_found/forms.py
from django import forms
from .models import LostItem, FoundItem
from django.utils import timezone


class LostItemForm(forms.ModelForm):
    date_lost = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        initial=timezone.now().date()
    )

    class Meta:
        model = LostItem
        fields = ['title', 'description', 'category', 'location_lost',
                  'date_lost', 'image', 'contact_info', 'reward']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class FoundItemForm(forms.ModelForm):
    date_found = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        initial=timezone.now().date()
    )

    class Meta:
        model = FoundItem
        fields = ['title', 'description', 'category', 'location_found',
                  'date_found', 'image', 'contact_info']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class SearchForm(forms.Form):
    query = forms.CharField(required=False, max_length=100)
    category = forms.ChoiceField(
        choices=[('', 'All Categories')] + list(LostItem.CATEGORY_CHOICES),
        required=False
    )
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + list(LostItem.STATUS_CHOICES),
        required=False
    )
    date_range = forms.ChoiceField(
        choices=[
            ('', 'Any Time'),
            ('today', 'Today'),
            ('week', 'This Week'),
            ('month', 'This Month'),
        ],
        required=False
    )