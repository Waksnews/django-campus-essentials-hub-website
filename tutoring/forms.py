from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import datetime, date, time, timedelta
from .models import Tutor, Session, Review, Subject


class TutorRegistrationForm(forms.ModelForm):
    """Form for tutor registration"""
    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    class Meta:
        model = Tutor
        fields = [
            'primary_subject', 'subjects', 'year_of_study',
            'hourly_rate', 'bio', 'qualifications', 'teaching_experience',
            'profile_picture', 'contact_email', 'contact_phone',
            'preferred_contact'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Tell students about yourself, your teaching style, and why you\'re a great tutor...'
            }),
            'qualifications': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Relevant courses, certifications, achievements...'
            }),
            'teaching_experience': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Previous tutoring/teaching experience...'
            }),
            'hourly_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '5',
                'max': '100',
                'step': '5'
            }),
            'primary_subject': forms.Select(attrs={'class': 'form-select'}),
            'year_of_study': forms.Select(attrs={'class': 'form-select'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'preferred_contact': forms.Select(attrs={'class': 'form-select'}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'primary_subject': 'Primary Subject',
            'hourly_rate': 'Hourly Rate ($)',
            'teaching_experience': 'Teaching Experience',
        }
        help_texts = {
            'hourly_rate': 'Set your hourly rate (USD)',
            'contact_email': 'Optional: Different from your account email',
            'contact_phone': 'Optional: Phone number for contact',
        }

    def clean_hourly_rate(self):
        rate = self.cleaned_data.get('hourly_rate')
        if rate < 5:
            raise forms.ValidationError('Minimum hourly rate is $5')
        if rate > 100:
            raise forms.ValidationError('Maximum hourly rate is $100')
        return rate


class SessionBookingForm(forms.ModelForm):
    """Form for booking a tutoring session"""

    def __init__(self, *args, **kwargs):
        self.tutor = kwargs.pop('tutor', None)
        self.student = kwargs.pop('student', None)
        super().__init__(*args, **kwargs)

        # Set initial date to tomorrow
        self.fields['date'].initial = date.today() + timedelta(days=1)

        # Add time choices based on tutor availability
        if self.tutor:
            self.fields['date'].widget.attrs.update({
                'min': date.today().isoformat(),
                'max': (date.today() + timedelta(days=14)).isoformat(),
            })

    class Meta:
        model = Session
        fields = ['date', 'start_time', 'duration', 'subject', 'topic', 'location', 'location_details', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
                'min': '08:00',
                'max': '21:00',
            }),
            'duration': forms.Select(attrs={'class': 'form-select'}, choices=[
                (30, '30 minutes'),
                (60, '1 hour'),
                (90, '1.5 hours'),
                (120, '2 hours'),
                (180, '3 hours'),
            ]),
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'topic': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Calculus derivatives, Python functions, Organic chemistry...'
            }),
            'location': forms.Select(attrs={'class': 'form-select'}),
            'location_details': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Room 205, Library 3rd floor, Zoom link...'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Specific topics you want to cover, questions you have, etc.'
            }),
        }
        labels = {
            'duration': 'Session Duration',
            'location_details': 'Specific Location/Details',
        }

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        start_time = cleaned_data.get('start_time')
        duration = cleaned_data.get('duration')

        if date and start_time and duration and self.tutor:
            # Calculate end time
            from datetime import datetime, timedelta
            start_datetime = datetime.combine(date, start_time)
            end_datetime = start_datetime + timedelta(minutes=duration)
            end_time = end_datetime.time()

            # Check if date is in the past
            if date < date.today():
                raise forms.ValidationError('Cannot book sessions in the past.')

            # Check if date is too far in future
            if date > date.today() + timedelta(days=14):
                raise forms.ValidationError('Sessions can only be booked up to 2 weeks in advance.')

            # Check tutor availability for that day/time
            day_name = date.strftime('%A').lower()
            available_hours = self.tutor.availability_slots.get(day_name, [])

            start_hour = start_time.hour
            end_hour = end_time.hour + (1 if end_time.minute > 0 else 0)

            # Check if chosen time is within available hours
            if not any(start_hour <= hour < end_hour for hour in available_hours):
                raise forms.ValidationError(
                    f'Tutor is not available at this time. Available hours: {", ".join(str(h) + ":00" for h in available_hours)}'
                )

            # Check for scheduling conflicts
            conflicting_session = Session.objects.filter(
                tutor=self.tutor,
                date=date,
                start_time__lt=end_time,
                end_time__gt=start_time,
                status__in=['pending', 'confirmed']
            ).exists()

            if conflicting_session:
                raise forms.ValidationError('This time slot is already booked. Please choose another time.')

        return cleaned_data


class ReviewForm(forms.ModelForm):
    """Form for reviewing a tutor"""

    class Meta:
        model = Review
        fields = ['rating', 'knowledge', 'teaching_skill', 'communication', 'punctuality', 'comment']
        widgets = {
            'rating': forms.RadioSelect(choices=[
                (5, '⭐⭐⭐⭐⭐ Excellent'),
                (4, '⭐⭐⭐⭐ Very Good'),
                (3, '⭐⭐⭐ Good'),
                (2, '⭐⭐ Fair'),
                (1, '⭐ Poor'),
            ]),
            'knowledge': forms.HiddenInput(),
            'teaching_skill': forms.HiddenInput(),
            'communication': forms.HiddenInput(),
            'punctuality': forms.HiddenInput(),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Share your experience with this tutor. What went well? What could be improved?'
            }),
        }
        labels = {
            'comment': 'Your Review',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial values for category ratings (same as overall rating)
        if 'rating' in self.data:
            rating = int(self.data.get('rating', 5))
            self.initial['knowledge'] = rating
            self.initial['teaching_skill'] = rating
            self.initial['communication'] = rating
            self.initial['punctuality'] = rating


class TutorUpdateForm(forms.ModelForm):
    """Form for updating tutor profile"""

    class Meta:
        model = Tutor
        fields = ['hourly_rate', 'bio', 'qualifications', 'teaching_experience',
                  'is_available', 'contact_email', 'contact_phone', 'preferred_contact']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'qualifications': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'teaching_experience': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'hourly_rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'preferred_contact': forms.Select(attrs={'class': 'form-select'}),
        }