# resources/forms.py
from django import forms
from .models import Resource, ResourceReview

class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['title', 'description', 'resource_type', 'subject', 'course_code', 'file', 'thumbnail']

class ReviewForm(forms.ModelForm):
    class Meta:
        model = ResourceReview
        fields = ['rating', 'comment']