from django import forms
from django.utils import timezone
from .models import Job, JobApplication


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'description', 'category', 'location', 'budget', 'budget_type', 'duration',
                  'skills_required']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Web Developer Needed',
                'autofocus': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe the job in detail...'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Campus Library, Online, or Remote'
            }),
            'budget': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
            'budget_type': forms.Select(attrs={'class': 'form-select'}),
            'duration': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2 weeks, 1 month, Flexible hours'
            }),
            'skills_required': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'List required skills (one per line or comma separated)...'
            }),
        }

    def clean_budget(self):
        budget = self.cleaned_data.get('budget')
        if budget <= 0:
            raise forms.ValidationError("Budget must be greater than 0.")
        return budget


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ['cover_letter', 'proposed_rate']
        widgets = {
            'cover_letter': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Explain why you are the best candidate for this job...'
            }),
            'proposed_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': 'Propose your rate (optional for fixed jobs)'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.job = kwargs.pop('job', None)
        super().__init__(*args, **kwargs)

        if self.job and self.job.budget_type == 'fixed':
            self.fields['proposed_rate'].required = False
            self.fields['proposed_rate'].help_text = 'Optional for fixed-budget jobs'
        elif self.job and self.job.budget_type == 'hourly':
            self.fields['proposed_rate'].required = True
            self.fields['proposed_rate'].help_text = 'Required for hourly jobs'

    def clean_proposed_rate(self):
        proposed_rate = self.cleaned_data.get('proposed_rate')
        if self.job and self.job.budget_type == 'hourly' and not proposed_rate:
            raise forms.ValidationError("Please propose an hourly rate for hourly jobs.")
        if proposed_rate and proposed_rate <= 0:
            raise forms.ValidationError("Proposed rate must be greater than 0.")
        return proposed_rate


class JobFilterForm(forms.Form):
    category = forms.ChoiceField(
        choices=[('', 'All Categories')] + list(Job.CATEGORY_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Location...'
        })
    )
    budget_min = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Min budget',
            'step': '0.01'
        })
    )
    budget_max = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Max budget',
            'step': '0.01'
        })
    )
    sort_by = forms.ChoiceField(
        choices=[
            ('-created_at', 'Newest First'),
            ('created_at', 'Oldest First'),
            ('budget', 'Budget: Low to High'),
            ('-budget', 'Budget: High to Low'),
        ],
        required=False,
        initial='-created_at',
        widget=forms.Select(attrs={'class': 'form-select'})
    )