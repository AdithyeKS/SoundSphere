from django.contrib import messages
from django.shortcuts import redirect


def seller_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Please log in as a Seller to access the Seller Dashboard.")
            return redirect('sellers:login')
        if hasattr(request.user, 'profile') and request.user.profile.is_seller:
            return view_func(request, *args, **kwargs)
        messages.error(request, "Access restricted to registered Sellers.")
        return redirect('products:home')
    return _wrapped_view

def seller_approved_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Please log in as a Seller.")
            return redirect('sellers:login')
        if hasattr(request.user, 'seller_profile'):
            if not request.user.seller_profile.is_approved:
                messages.warning(request, "Your seller application is currently pending Admin approval. Product management is disabled until approved.")
                return redirect('sellers:dashboard')
            return view_func(request, *args, **kwargs)
        messages.error(request, "Access restricted to registered Sellers.")
        return redirect('products:home')
    return _wrapped_view

