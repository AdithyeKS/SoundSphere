from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def seller_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Session expired or authentication required. Please log in as a Seller to access the Seller Dashboard.")
            resp = redirect(f"/seller/login/?next={request.path}")
            resp['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
            resp['Pragma'] = 'no-cache'
            resp['Expires'] = '0'
            return resp
        if (hasattr(request.user, 'profile') and request.user.profile.is_seller) or hasattr(request.user, 'seller_profile'):
            response = view_func(request, *args, **kwargs)
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            return response
        messages.error(request, "Access restricted to registered Sellers.")
        resp = redirect('products:home')
        resp['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
        resp['Pragma'] = 'no-cache'
        resp['Expires'] = '0'
        return resp
    return _wrapped_view

def seller_approved_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Session expired or authentication required. Please log in as a Seller.")
            resp = redirect(f"/seller/login/?next={request.path}")
            resp['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
            resp['Pragma'] = 'no-cache'
            resp['Expires'] = '0'
            return resp
        if hasattr(request.user, 'seller_profile'):
            if not request.user.seller_profile.is_approved:
                messages.warning(request, "Your seller application is currently pending Admin approval. Product management is disabled until approved.")
                resp = redirect('sellers:dashboard')
                resp['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
                resp['Pragma'] = 'no-cache'
                resp['Expires'] = '0'
                return resp
            response = view_func(request, *args, **kwargs)
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            return response
        messages.error(request, "Access restricted to registered Sellers.")
        resp = redirect('products:home')
        resp['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
        resp['Pragma'] = 'no-cache'
        resp['Expires'] = '0'
        return resp
    return _wrapped_view
