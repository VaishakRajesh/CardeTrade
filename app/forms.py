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
    Form for new user registration with role-based verification.

    Extends Django's UserCreationForm with additional fields:
    - email: Required for account notifications
    - phone: Optional contact number
    - address: Optional physical address
    - region: Optional geographic region
    - role: Selection between farmer/trader/pm
    - verification_doc: Required for Farmer & Product Manager roles

    Verification rules:
    - Farmers must upload proof (business license, land docs, etc.)
    - Product Managers must upload credentials/certification
    - Traders are auto-verified (no document needed)
    """

    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)
    region = forms.CharField(max_length=100, required=False)
    verification_doc = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-premium', 'accept': '.pdf,.jpg,.jpeg,.png'}),
        help_text='Upload business license, ID proof, or certification (PDF/JPG/PNG)'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'role', 'phone', 'address', 'region', 'verification_doc']

    def __init__(self, *args, **kwargs):
        """Remove help text from username and password fields."""
        super().__init__(*args, **kwargs)
        for field_name in ('username', 'email', 'password1', 'password2'):
            self.fields[field_name].help_text = None

    def clean_verification_doc(self):
        """Require verification_doc for Farmer and Product Manager roles."""
        doc = self.cleaned_data.get('verification_doc')
        role = self.data.get('role') or self.initial.get('role')
        if role in ('farmer', 'product_manager') and not doc:
            raise forms.ValidationError('Verification document is required for this role.')
        return doc


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
