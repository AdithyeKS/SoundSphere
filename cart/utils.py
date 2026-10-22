from .models import Cart


def get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        # Merge session cart if exists
        session_id = request.session.session_key
        if session_id:
            try:
                session_cart = Cart.objects.get(session_id=session_id, user__isnull=True)
                for item in session_cart.items.all():
                    existing_item, item_created = cart.items.get_or_create(
                        product=item.product,
                        defaults={'quantity': item.quantity}
                    )
                    if not item_created:
                        existing_item.quantity += item.quantity
                        existing_item.save()
                session_cart.delete()
            except Cart.DoesNotExist:
                pass
        return cart
    else:
        if not request.session.session_key:
            request.session.create()
        session_id = request.session.session_key
        cart, _ = Cart.objects.get_or_create(session_id=session_id, user__isnull=True)
        return cart
