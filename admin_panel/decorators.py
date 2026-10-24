from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def admin_required(view_func):
    """
    Ensures the user is authenticated and possesses administrator / staff privileges.
    If unauthenticated or session has expired, cleanly redirects to /accounts/login/?role=admin
    with a clear notification, preventing back-button exploits and session leakage.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Session expired or authentication required. Please sign in with your Admin credentials.")
            resp = redirect(f"/accounts/login/?role=admin&next={request.path}")
            resp['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
            resp['Pragma'] = 'no-cache'
            resp['Expires'] = '0'
            return resp
        if not (request.user.is_staff or request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role == 'admin')):
            messages.error(request, "Access restricted. Administrator privileges required to access the Admin Control Panel.")
            resp = redirect('products:home')
            resp['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
            resp['Pragma'] = 'no-cache'
            resp['Expires'] = '0'
            return resp
        response = view_func(request, *args, **kwargs)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
    return _wrapped_view
