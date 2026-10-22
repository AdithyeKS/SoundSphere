import re

from django import forms
from django.contrib.auth.forms import (
    PasswordResetForm,
    SetPasswordForm,
    UserCreationForm,
)
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import ShippingAddress, UserProfile


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'you@example.com'}))
    first_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'placeholder': 'Last Name'}))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('phone', 'bio')

class ShippingAddressForm(forms.ModelForm):
    class Meta:
        model = ShippingAddress
        fields = (
            'full_name',
            'phone_number',
            'street_address',
            'apartment_address',
            'city',
            'state',
            'postal_code',
            'country',
            'is_default',
        )


class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label="Email Address",
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'custom-input',
            'placeholder': 'Enter your registered email address',
            'autocomplete': 'email',
            'required': 'required'
        })
    )


class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'custom-input',
            'placeholder': 'Enter new password',
            'autocomplete': 'new-password',
            'required': 'required'
        })
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'custom-input',
            'placeholder': 'Confirm new password',
            'autocomplete': 'new-password',
            'required': 'required'
        })
    )

    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1')
        if not password:
            raise ValidationError("Password is required.")

        errors = []
        if len(password) < 8:
            errors.append("at least 8 characters")
        if not re.search(r'[A-Z]', password):
            errors.append("one uppercase letter (A-Z)")
        if not re.search(r'[a-z]', password):
            errors.append("one lowercase letter (a-z)")
        if not re.search(r'[0-9]', password):
            errors.append("one number (0-9)")
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>/?]', password):
            errors.append("one special symbol (e.g. @, #, $, !)")

        if errors:
            raise ValidationError(
                "Password requirement failed: Please include " + ", ".join(errors) + "."
            )
        return password

