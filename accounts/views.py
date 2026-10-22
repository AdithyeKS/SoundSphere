import re
import smtplib
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import (
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from dotenv import dotenv_values

from .forms import (
    CustomPasswordResetForm,
    CustomSetPasswordForm,
    ProfileUpdateForm,
    ShippingAddressForm,
    UserUpdateForm,
)
from .models import CustomerFeedback, SellerProfile, ShippingAddress, UserProfile


def register_view(request):
    if request.user.is_authenticated:
        return redirect('products:home')
    
    if request.method == 'POST':
        role = request.POST.get('role', 'customer').strip().lower()
        if role not in ['customer', 'seller']:
            messages.error(request, "Admin registration is restricted. Only existing administrator accounts can access the Admin Panel.")
            return render(request, 'accounts/register.html', {'role': 'customer'})

        first_name = request.POST.get('first_name', '').strip().title()
        last_name = request.POST.get('last_name', '').strip().title()
        email = request.POST.get('email', '').strip().lower()
        phone = request.POST.get('phone', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        # Seller specific fields
        store_name = request.POST.get('store_name', '').strip()
        tagline = request.POST.get('tagline', '').strip()
        store_description = request.POST.get('store_description', '').strip()
        tax_id = request.POST.get('tax_id', '').strip()
        location = request.POST.get('location', '').strip()
        state = request.POST.get('state', '').strip()
        logo_file = request.FILES.get('logo')

        # Form Data Context for Preserving Inputs on Error
        form_data = {
            'role': role,
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'phone': phone,
            'store_name': store_name,
            'tagline': tagline,
            'store_description': store_description,
            'tax_id': tax_id,
            'location': location,
            'state': state,
        }

        # Basic Required Fields Validation
        if not first_name or not last_name:
            messages.error(request, "Please enter both First Name and Last Name.")
            return render(request, 'accounts/register.html', form_data)

        if not email or not password1 or not password2:
            messages.error(request, "Please fill in all required registration fields.")
            return render(request, 'accounts/register.html', form_data)

        # Email Format Validation
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            messages.error(request, "Please enter a valid email address (e.g. user@domain.com).")
            return render(request, 'accounts/register.html', form_data)

        # Phone Number 10-Digit Format Validation
        if not phone:
            messages.error(request, "Please enter your 10-digit mobile phone number.")
            return render(request, 'accounts/register.html', form_data)

        phone_digits = re.sub(r'\D', '', phone)
        if len(phone_digits) < 10 or len(phone_digits) > 12:
            messages.error(request, "Please enter a valid 10-digit mobile phone number.")
            return render(request, 'accounts/register.html', form_data)

        # Passwords Match Validation
        if password1 != password2:
            messages.error(request, "Password and Confirm Password do not match.")
            return render(request, 'accounts/register.html', form_data)

        # Password Complexity Validation
        password_errors = []
        if len(password1) < 8:
            password_errors.append("at least 8 characters")
        if not re.search(r'[A-Z]', password1):
            password_errors.append("one uppercase letter (A-Z)")
        if not re.search(r'[a-z]', password1):
            password_errors.append("one lowercase letter (a-z)")
        if not re.search(r'[0-9]', password1):
            password_errors.append("one number (0-9)")
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>/?]', password1):
            password_errors.append("one special symbol (e.g. @, #, $, !)")

        if password_errors:
            error_msg = "Password requirement failed: Please include " + ", ".join(password_errors) + "."
            messages.error(request, error_msg)
            return render(request, 'accounts/register.html', form_data)

        if User.objects.filter(email=email).exists():
            messages.error(request, "An account with this email address is already registered.")
            return render(request, 'accounts/register.html', form_data)

        # Handle Seller role specific field validation
        if role == 'seller':
            if not store_name or not store_description or not tax_id or not location or not state:
                messages.error(request, "Please fill in all required Seller fields (Brand Name, Brand Description, Business ID, Location, and State).")
                return render(request, 'accounts/register.html', form_data)

            if SellerProfile.objects.filter(store_name=store_name).exists():
                messages.error(request, f"Brand Name '{store_name}' is already registered.")
                return render(request, 'accounts/register.html', form_data)

        # Derive unique username automatically from email
        base_username = email.split('@')[0]
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1

        # Create base User record
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name
        )

        # Update UserProfile
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = role
        if phone:
            profile.phone = phone
        profile.save()

        # Handle Seller role profile creation
        if role == 'seller':
            SellerProfile.objects.create(
                user=user,
                store_name=store_name,
                tagline=tagline or None,
                store_description=store_description,
                phone=phone or "N/A",
                tax_id=tax_id,
                location=location,
                state=state,
                logo=logo_file,
                status='pending'
            )

        # Auto login
        login(request, user)

        if role == 'seller':
            messages.success(request, f"Welcome Seller {first_name or username}! Your seller application has been submitted and is currently pending Admin review.")
            return redirect('sellers:dashboard')
        else:
            messages.success(request, f"Welcome to SoundSphere, {first_name or username}! Account created.")
            return redirect('products:home')

    return render(request, 'accounts/register.html', {'role': request.GET.get('role', 'customer')})

def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('admin_panel:dashboard')
        elif hasattr(request.user, 'profile') and request.user.profile.is_seller:
            return redirect('sellers:dashboard')
        return redirect('products:home')

    if request.method == 'POST':
        login_input = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        selected_role = request.POST.get('role', 'customer').strip().lower()

        user_obj = User.objects.filter(Q(email__iexact=login_input) | Q(username__iexact=login_input)).first()
        target_username = user_obj.username if user_obj else login_input

        user = authenticate(username=target_username, password=password)
        if user is not None:
            user_is_seller = (hasattr(user, 'profile') and user.profile.is_seller) or hasattr(user, 'seller_profile')
            user_is_admin = user.is_staff or user.is_superuser

            # Restrict Customer accounts from logging in via Seller portal
            if selected_role == 'seller' and not user_is_seller and not user_is_admin:
                messages.error(request, "Access restricted. This account is registered as a Customer. Please switch to the Customer login tab.")
                return render(request, 'accounts/login.html', {'role': 'seller', 'login_input': login_input})

            # Restrict Seller accounts from logging in via Customer portal
            if selected_role == 'customer' and user_is_seller and not user_is_admin:
                messages.error(request, "Access restricted. This account is registered as a Seller. Please switch to the Seller login tab.")
                return render(request, 'accounts/login.html', {'role': 'customer', 'login_input': login_input})

            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)

            # Automatic Smart Redirect based on user privileges
            if user_is_admin:
                return redirect('admin_panel:dashboard')
            elif user_is_seller:
                return redirect('sellers:dashboard')
            else:
                return redirect('products:home')
        messages.error(request, "Invalid email/username or password.")
        return render(request, 'accounts/login.html', {'role': selected_role, 'login_input': login_input})
    else:
        role = request.GET.get('role', 'customer')
        return render(request, 'accounts/login.html', {'role': role})

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('products:home')

@login_required
def profile_view(request):
    addresses = ShippingAddress.objects.filter(user=request.user)
    return render(request, 'accounts/profile.html', {
        'addresses': addresses
    })

@login_required
def edit_profile_view(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('accounts:profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    return render(request, 'accounts/edit_profile.html', {
        'u_form': u_form,
        'p_form': p_form
    })

@login_required
def add_address_view(request):
    if request.method == 'POST':
        form = ShippingAddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, "Shipping address added successfully!")
            next_url = request.GET.get('next', 'accounts:profile')
            return redirect(next_url)
    else:
        form = ShippingAddressForm()
    return render(request, 'accounts/address_form.html', {'form': form})

@login_required
def delete_address_view(request, address_id):
    address = get_object_or_404(ShippingAddress, id=address_id, user=request.user)
    address.delete()
    messages.success(request, "Address removed successfully.")
    return redirect('accounts:profile')

def feedback_view(request):
    if not request.user.is_authenticated:
        messages.info(request, "Please login or register to send customer feedback.")
        return redirect(f"/accounts/login/?next={request.path}")

    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        category = request.POST.get('category', 'general')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        rating = request.POST.get('rating', 5)

        CustomerFeedback.objects.create(
            user=request.user,
            name=name,
            email=email,
            category=category,
            subject=subject,
            message=message,
            rating=int(rating)
        )
        messages.success(request, "Thank you for sending your feedback! We appreciate your thoughts.")
        return redirect('products:home')

    return render(request, 'accounts/feedback.html')


class CustomPasswordResetView(PasswordResetView):
    template_name = 'accounts/password_reset.html'
    form_class = CustomPasswordResetForm
    email_template_name = 'accounts/emails/password_reset_email.txt'
    html_email_template_name = 'accounts/emails/password_reset_email.html'
    subject_template_name = 'accounts/emails/password_reset_subject.txt'
    success_url = reverse_lazy('accounts:password_reset_done')

    def form_valid(self, form):
        env_path = Path(settings.BASE_DIR) / '.env'
        env_vals = dotenv_values(env_path) if env_path.exists() else {}

        email_user = getattr(settings, 'EMAIL_HOST_USER', '') or env_vals.get('EMAIL_HOST_USER', '')
        email_pass = getattr(settings, 'EMAIL_HOST_PASSWORD', '') or env_vals.get('EMAIL_HOST_PASSWORD', '')

        if not email_user or not email_pass:
            messages.error(
                self.request,
                "Gmail SMTP credentials are not configured yet. Please add EMAIL_HOST_USER and EMAIL_HOST_PASSWORD (16-character Google App Password) in your .env file."
            )
            return render(self.request, self.template_name, {'form': form})

        # Dynamically inject credentials into settings if not already refreshed
        settings.EMAIL_HOST_USER = email_user
        settings.EMAIL_HOST_PASSWORD = email_pass
        if not getattr(settings, 'DEFAULT_FROM_EMAIL', '') or 'noreply' in getattr(settings, 'DEFAULT_FROM_EMAIL', ''):
            settings.DEFAULT_FROM_EMAIL = env_vals.get('DEFAULT_FROM_EMAIL') or f"SoundSphere Support <{email_user}>"

        # Explicitly pass current host and protocol so links in emails are always valid
        self.extra_email_context = {
            'domain': self.request.get_host(),
            'protocol': 'https' if self.request.is_secure() else 'http',
        }

        try:
            return super().form_valid(form)
        except (smtplib.SMTPException, OSError) as err:
            messages.error(
                self.request,
                f"Failed to dispatch email via Gmail SMTP: {err!s}. Please check your Gmail address and 16-character App Password."
            )
            return render(self.request, self.template_name, {'form': form})



class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'accounts/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    form_class = CustomSetPasswordForm
    success_url = reverse_lazy('accounts:password_reset_complete')

    def form_valid(self, form):
        messages.success(self.request, "Your password has been successfully reset! You can now log in.")
        return super().form_valid(form)


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'accounts/password_reset_complete.html'

