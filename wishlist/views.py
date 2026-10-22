from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from cart.models import CartItem
from cart.utils import get_or_create_cart
from products.models import Product

from .models import Wishlist, WishlistItem


@login_required
def wishlist_view(request):
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    items = wishlist.items.select_related('product')
    return render(request, 'wishlist/wishlist.html', {
        'items': items
    })

def toggle_wishlist_view(request, product_id):
    if not request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'require_login': True,
                'redirect_url': f'/accounts/login/?next={request.META.get("HTTP_REFERER", "/")}',
                'message': 'Please log in or register to add items to your wishlist.'
            })
        messages.info(request, "Please log in or register to manage your wishlist.")
        return redirect(f'/accounts/login/?next={request.META.get("HTTP_REFERER", "/")}')

    product = get_object_or_404(Product, id=product_id)
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    
    item, created = WishlistItem.objects.get_or_create(wishlist=wishlist, product=product)
    
    if not created:
        item.delete()
        added = False
        msg = f"Removed {product.name} from your wishlist."
    else:
        added = True
        msg = f"Added {product.name} to your wishlist!"

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'added': added,
            'message': msg,
            'wishlist_count': wishlist.items.count()
        })

    messages.success(request, msg)
    return redirect(request.META.get('HTTP_REFERER', 'wishlist:view'))

@login_required
def move_to_cart_view(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    
    # Remove from wishlist
    WishlistItem.objects.filter(wishlist=wishlist, product=product).delete()

    # Add to cart
    cart = get_or_create_cart(request)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()

    messages.success(request, f"Moved {product.name} from wishlist to your cart!")
    return redirect('cart:detail')
