from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from products.models import Product

from .models import CartItem
from .utils import get_or_create_cart


def cart_detail_view(request):
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to your account to view your shopping cart.")
        return redirect('/accounts/login/?next=/cart/')

    if request.user.is_staff:
        messages.info(request, "Admin Viewer Mode: Cart and checkout operations are disabled for staff accounts.")
    elif hasattr(request.user, 'profile') and request.user.profile.is_seller:
        messages.info(request, "Merchant Viewer Mode: Cart and checkout operations are disabled for brand merchant accounts.")

    cart = get_or_create_cart(request)
    coupon_code = request.session.get('coupon_code', '')
    discount_amount = Decimal('0.00')
    if coupon_code:
        if coupon_code == 'SOUND10':
            discount_amount = (cart.subtotal * Decimal('0.10')).quantize(Decimal('0.01'))
        elif coupon_code == 'VIP20':
            discount_amount = (cart.subtotal * Decimal('0.20')).quantize(Decimal('0.01'))

    final_total = max(Decimal('0.00'), cart.grand_total - discount_amount)

    return render(request, 'cart/cart.html', {
        'cart': cart,
        'final_total': final_total,
        'discount_amount': discount_amount,
        'coupon_code': coupon_code,
    })

def apply_coupon_view(request):
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        cart = get_or_create_cart(request)
        if code in ['SOUND10', 'VIP20']:
            request.session['coupon_code'] = code
            rate = Decimal('0.10') if code == 'SOUND10' else Decimal('0.20')
            discount = (cart.subtotal * rate).quantize(Decimal('0.01'))
            final_total = max(Decimal('0.00'), cart.grand_total - discount)
            msg = f"Promo code '{code}' applied successfully! Saved ₹{discount}."
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': msg,
                    'coupon_code': code,
                    'discount_amount': str(discount),
                    'final_total': str(final_total),
                })
            messages.success(request, msg)
        elif not code:
            request.session.pop('coupon_code', None)
            msg = "Coupon code removed."
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': msg,
                    'coupon_code': '',
                    'discount_amount': '0.00',
                    'final_total': str(cart.grand_total),
                })
            messages.info(request, msg)
        else:
            msg = f"Invalid promo code '{code}'. Try SOUND10 or VIP20."
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': msg})
            messages.error(request, msg)
    return redirect('cart:detail')

def cart_add_view(request, product_id):
    if not request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'require_login': True,
                'redirect_url': f'/accounts/login/?next={request.META.get("HTTP_REFERER", "/")}',
                'message': 'Please log in or register to add items to your cart.'
            })
        messages.info(request, "Please log in or register to add items to your cart.")
        return redirect(f'/accounts/login/?next={request.META.get("HTTP_REFERER", "/")}')

    user_is_seller = hasattr(request.user, 'profile') and request.user.profile.is_seller
    if request.user.is_staff or user_is_seller:
        role_label = "Admin" if request.user.is_staff else "Brand Merchant"
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f'{role_label} Viewer Mode: Merchant accounts cannot add items to cart or make purchases.'
            })
        messages.warning(request, f"{role_label} Viewer Mode: {role_label} accounts cannot add items to cart.")
        return redirect(request.META.get('HTTP_REFERER', 'products:list'))

    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart = get_or_create_cart(request)
    
    quantity = max(int(request.POST.get('quantity', 1)), 1)

    if quantity > product.stock:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': f"Only {product.stock} items available in stock."})
        messages.error(request, f"Only {product.stock} items available in stock.")
        return redirect('cart:detail')

    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        if item.quantity + quantity > product.stock:
            item.quantity = product.stock
        else:
            item.quantity += quantity
    else:
        item.quantity = quantity
    item.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f"Added {product.name} to your cart!",
            'cart_item_count': cart.total_items
        })

    messages.success(request, f"Added {product.name} to your cart!")
    return redirect('cart:detail')

def buy_now_view(request, product_id):
    """Instant Buy Now: adds item to cart & redirects immediately to checkout."""
    if not request.user.is_authenticated:
        product = get_object_or_404(Product, id=product_id)
        messages.info(request, "Please log in or register to purchase products.")
        return redirect(f'/accounts/login/?next=/product/{product.slug}/')

    user_is_seller = hasattr(request.user, 'profile') and request.user.profile.is_seller
    if request.user.is_staff or user_is_seller:
        role_label = "Admin" if request.user.is_staff else "Brand Merchant"
        messages.warning(request, f"{role_label} Viewer Mode: {role_label} accounts cannot purchase products.")
        return redirect(request.META.get('HTTP_REFERER', 'products:list'))

    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart = get_or_create_cart(request)
    
    quantity = int(request.POST.get('quantity', 1))
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += quantity
    else:
        item.quantity = quantity
    item.save()

    return redirect('orders:checkout')

@login_required(login_url='accounts:login')
def cart_update_view(request, item_id):
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    
    quantity = int(request.POST.get('quantity', 1))
    if quantity <= 0:
        item.delete()
        msg = f"Removed {item.product.name} from cart."
    else:
        if quantity > item.product.stock:
            quantity = item.product.stock
            messages.warning(request, f"Adjusted to maximum available stock ({item.product.stock}).")
        item.quantity = quantity
        item.save()
        msg = "Cart updated successfully."

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': msg,
            'cart_item_count': cart.total_items,
            'subtotal': str(cart.subtotal),
            'tax': str(cart.tax),
            'shipping': str(cart.shipping),
            'grand_total': str(cart.grand_total)
        })

    messages.success(request, msg)
    return redirect('cart:detail')

@login_required(login_url='accounts:login')
def cart_remove_view(request, item_id):
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    product_name = item.product.name
    item.delete()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f"Removed {product_name} from your cart.",
            'cart_item_count': cart.total_items,
            'subtotal': str(cart.subtotal),
            'tax': str(cart.tax),
            'shipping': str(cart.shipping),
            'grand_total': str(cart.grand_total)
        })

    messages.success(request, f"Removed {product_name} from your cart.")
    return redirect('cart:detail')

