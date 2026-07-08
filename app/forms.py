"""
CardeTrade Django Forms - All Platform Forms

This module contains all the forms used in the CardeTrade platform.
Forms handle:
- User input validation
- Data cleaning
- Widget configuration (HTML rendering)
- Error message handling

Form Types:
- RegistrationForm: New user account creation
- LoginForm: User authentication
- UserProfileForm: Profile editing

All forms use Django's ModelForm where applicable for automatic
field generation and validation.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model

User = get_user_model()


class RegistrationForm(UserCreationForm):
    """
    Form for new user registration.

    Extends Django's UserCreationForm with additional fields:
    - email: Required for account notifications
    - phone: Optional contact number
    - address: Optional physical address
    - region: Optional geographic region
    - role: Selection between farmer/trader

    The help text for username and password fields is removed
    for a cleaner UI.
    """

    email = forms.EmailField(required=True)  # Required for notifications
    phone = forms.CharField(max_length=20, required=False)  # Optional contact
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)  # Optional address
    region = forms.CharField(max_length=100, required=False)  # Optional region

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'role', 'phone', 'address', 'region']

    def __init__(self, *args, **kwargs):
        """Remove help text from username and password fields."""
        super().__init__(*args, **kwargs)
        # Hide default Django help text for cleaner UI
        for field_name in ('username', 'email', 'password1', 'password2'):
            self.fields[field_name].help_text = None


class LoginForm(AuthenticationForm):
    """
    Form for user login/authentication.

    Uses email as the primary identifier instead of username.
    Customizes Django's AuthenticationForm with Bootstrap 5 styling
    and placeholder text for better UX.
    """

    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address', 'autocomplete': 'email'})
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password', 'autocomplete': 'current-password'})
    )


class UserProfileForm(forms.ModelForm):
    """
    Form for editing user profile information.

    Allows users to update:
    - first_name, last_name: Display name
    - email: Contact email
    - phone: Contact number
    - address: Physical address
    - region: Geographic region

    Uses ModelForm for automatic field generation from User model.
    """

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'region']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 2}),  # Multi-line address field
        }
