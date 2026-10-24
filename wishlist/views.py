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
    items = wishlist.items.select_related('product', 'product__category')
    total_value = sum(item.product.current_price for item in items)
    return render(request, 'wishlist/wishlist.html', {
        'items': items,
        'total_items': items.count(),
        'total_value': total_value,
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

    user_is_seller = hasattr(request.user, 'profile') and request.user.profile.is_seller
    if request.user.is_staff or user_is_seller:
        role_label = "Admin" if request.user.is_staff else "Brand Merchant"
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f'{role_label} Viewer Mode: Wishlist is restricted to customer accounts.'
            })
        messages.warning(request, f"{role_label} Viewer Mode: Wishlist is restricted to customer accounts.")
        return redirect(request.META.get('HTTP_REFERER', 'products:list'))

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

@login_required
def move_all_to_cart_view(request):
    if request.method == 'POST':
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        items = list(wishlist.items.select_related('product'))
        if not items:
            messages.info(request, "Your wishlist is empty.")
            return redirect('wishlist:view')
            
        cart = get_or_create_cart(request)
        moved_count = 0
        for item in items:
            if item.product.is_active and item.product.stock > 0:
                cart_item, created = CartItem.objects.get_or_create(cart=cart, product=item.product)
                if not created:
                    cart_item.quantity += 1
                    cart_item.save()
                item.delete()
                moved_count += 1
                
        if moved_count > 0:
            messages.success(request, f"Moved {moved_count} item{'s' if moved_count > 1 else ''} from your wishlist into your shopping cart!")
            return redirect('cart:detail')
        else:
            messages.warning(request, "No in-stock items were available to move.")
            return redirect('wishlist:view')
    return redirect('wishlist:view')

@login_required
def clear_wishlist_view(request):
    if request.method == 'POST':
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        count = wishlist.items.count()
        wishlist.items.all().delete()
        messages.info(request, f"Cleared {count} item{'s' if count != 1 else ''} from your wishlist.")
    return redirect('wishlist:view')
