# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
import re
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    student_id = forms.CharField(max_length=20, required=True)
    university = forms.CharField(max_length=200, required=True)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'student_id', 'university', 'course',
                  'year_of_study', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data['email']
        # Check if email ends with .ac.ke (Kenyan university email)
        if not email.endswith('.ac.ke'):
            raise ValidationError("Please use your university email address (.ac.ke)")

        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered")
        return email

    def clean_student_id(self):
        student_id = self.cleaned_data['student_id']
        # Basic validation for student ID format
        if not re.match(r'^[A-Za-z0-9/-]+$', student_id):
            raise ValidationError("Enter a valid student ID")
        return student_id


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number',
                  'student_id', 'university', 'course', 'year_of_study', 'bio',
                  'profile_picture', 'location')


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number',
                  'student_id', 'university', 'course', 'year_of_study',
                  'bio', 'profile_picture', 'location']