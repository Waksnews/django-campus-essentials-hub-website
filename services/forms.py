# services/forms.py
from django import forms
from .models import Service, ServiceReview

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['name', 'description', 'category', 'location', 'contact_number', 'contact_email', 'website', 'opening_hours', 'price_range']

class ServiceReviewForm(forms.ModelForm):
    class Meta:
        model = ServiceReview
        fields = ['rating', 'comment']