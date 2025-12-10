# tutoring/forms.py
from django import forms
from .models import Tutor, Session, Review


class TutorRegistrationForm(forms.ModelForm):
    subjects = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'e.g., Programming, Calculus, Physics'}),
        help_text="Enter subjects separated by commas"
    )

    class Meta:
        model = Tutor
        fields = ['subjects', 'primary_subject', 'year_of_study',
                  'hourly_rate', 'bio', 'qualifications', 'availability']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'qualifications': forms.Textarea(attrs={'rows': 3}),
            'availability': forms.Textarea(attrs={'rows': 3}),
        }


class SessionBookingForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text="Select date for the session"
    )
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time'}),
        help_text="Start time"
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time'}),
        help_text="End time"
    )

    class Meta:
        model = Session
        fields = ['subject', 'date', 'start_time', 'end_time',
                  'location', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError("End time must be after start time")

        return cleaned_data


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5, 'step': 1}),
            'comment': forms.Textarea(attrs={'rows': 3}),
        }