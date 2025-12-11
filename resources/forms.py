from django import forms
from django.core.validators import FileExtensionValidator
from .models import Resource, ResourceReview


class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = [
            'title', 'description', 'resource_type', 'subject',
            'course_code', 'course_name', 'file', 'thumbnail',
            'year', 'semester', 'instructor', 'tags'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Calculus I Lecture Notes',
                'autofocus': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe the resource in detail...'
            }),
            'resource_type': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'course_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., MATH101, CS202'
            }),
            'course_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Optional: Full course name'
            }),
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2023',
                'min': '2000',
                'max': '2030'
            }),
            'semester': forms.Select(attrs={'class': 'form-select'}),
            'instructor': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Optional: Professor/Instructor name'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., calculus, math, notes, midterm'
            }),
        }
        help_texts = {
            'file': 'Upload your resource file (PDF, DOC, PPT, ZIP, etc.)',
            'thumbnail': 'Optional: Upload a thumbnail image',
            'tags': 'Separate tags with commas',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].widget.attrs.update({'class': 'form-control'})
        self.fields['thumbnail'].widget.attrs.update({'class': 'form-control'})

        # Add file validation
        self.fields['file'].validators.append(
            FileExtensionValidator(
                allowed_extensions=['pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx',
                                    'txt', 'zip', 'rar', 'jpg', 'jpeg', 'png', 'mp4', 'mp3'],
                message='File type not supported. Please upload a valid file.'
            )
        )

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Limit file size to 100MB
            max_size = 100 * 1024 * 1024  # 100MB
            if file.size > max_size:
                raise forms.ValidationError(
                    f'File size must be under 100MB. Your file is {file.size / 1024 / 1024:.1f}MB.')
        return file


class ReviewForm(forms.ModelForm):
    class Meta:
        model = ResourceReview
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(choices=[
                (5, '⭐⭐⭐⭐⭐ Excellent'),
                (4, '⭐⭐⭐⭐ Very Good'),
                (3, '⭐⭐⭐ Good'),
                (2, '⭐⭐ Fair'),
                (1, '⭐ Poor'),
            ]),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Share your experience with this resource...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rating'].widget.attrs.update({'class': 'form-check-input'})
        self.fields['rating'].label = 'Rating'


class ResourceSearchForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search resources...'
        })
    )
    resource_type = forms.ChoiceField(
        choices=[('', 'All Types')] + list(Resource.TYPE_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    subject = forms.ChoiceField(
        choices=[('', 'All Subjects')] + list(Resource.SUBJECT_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    course_code = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Course code...'
        })
    )
    sort_by = forms.ChoiceField(
        choices=[
            ('-created_at', 'Newest First'),
            ('created_at', 'Oldest First'),
            ('-downloads', 'Most Popular'),
            ('-average_rating', 'Highest Rated'),
            ('title', 'Title A-Z'),
            ('-title', 'Title Z-A'),
        ],
        required=False,
        initial='-created_at',
        widget=forms.Select(attrs={'class': 'form-select'})
    )