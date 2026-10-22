from .utils import get_or_create_cart


def cart_processor(request):
    try:
        cart = get_or_create_cart(request)
        return {
            'cart': cart,
            'cart_item_count': cart.total_items,
        }
    except Exception:  # noqa: BLE001
        return {
            'cart': None,
            'cart_item_count': 0,
        }
