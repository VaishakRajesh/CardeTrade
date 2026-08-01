"""
accounts/forms.py

Provides form classes for user registration, login,
and profile editing on the CardeTrade platform.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model

User = get_user_model()


# Form for new user registration with role and document upload
class RegistrationForm(UserCreationForm):
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

    # Remove default help text from standard auth fields
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ('username', 'email', 'password1', 'password2'):
            self.fields[field_name].help_text = None

    # Require verification document for farmer and product_manager roles
    def clean_verification_doc(self):
        doc = self.cleaned_data.get('verification_doc')
        role = self.data.get('role') or self.initial.get('role')
        if role in ('farmer', 'product_manager') and not doc:
            raise forms.ValidationError('Verification document is required for this role.')
        return doc


# Login form using email as the username field
class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address', 'autocomplete': 'email'})
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password', 'autocomplete': 'current-password'})
    )


# Form for users to edit their personal profile information
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'region']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 2}),
        }
