from django.utils.deprecation import MiddlewareMixin


class DisableBrowserCacheMiddleware(MiddlewareMixin):
    """
    Prevents browsers (especially Chrome/Edge/Safari) from serving cached pages
    from the bfcache (Back/Forward Cache) or disk cache after logout.
    Enforces 'no-cache, no-store, must-revalidate' on all authenticated pages
    and sensitive portals (admin, seller, accounts, checkout).
    """

    def process_response(self, request, response):
        path = request.path_info or ''
        is_sensitive_path = (
            path.startswith('/admin-panel/') or
            path.startswith('/admin/') or
            path.startswith('/seller/') or
            path.startswith('/accounts/') or
            path.startswith('/orders/') or
            path.startswith('/cart/') or
            path.startswith('/wishlist/')
        )
        is_authenticated = bool(getattr(request, 'user', None) and request.user.is_authenticated)

        if is_sensitive_path or is_authenticated:
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'

        return response
