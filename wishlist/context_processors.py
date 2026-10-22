import logging

from .models import Wishlist

logger = logging.getLogger(__name__)

def wishlist_processor(request):
    if request.user.is_authenticated:
        try:
            wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
            wishlist_ids = list(wishlist.items.values_list('product_id', flat=True))
            return {
                'wishlist_count': len(wishlist_ids),
                'wishlist_product_ids': wishlist_ids
            }
        except Exception as e:  # noqa: BLE001
            logger.debug("Error retrieving wishlist context: %s", e)
    return {
        'wishlist_count': 0,
        'wishlist_product_ids': []
    }
