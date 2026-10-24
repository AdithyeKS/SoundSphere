import logging
import smtplib
import uuid
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import BadHeaderError, send_mail
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import ShippingAddress
from cart.utils import get_or_create_cart
from products.models import Product

from .models import Order, OrderItem, Payment

logger = logging.getLogger(__name__)

def _get_discount_from_session(request, cart_subtotal):
    coupon_code = request.session.get('coupon_code', '')
    if coupon_code == 'SOUND10':
        return (cart_subtotal * Decimal('0.10')).quantize(Decimal('0.01'))
    elif coupon_code == 'VIP20':
        return (cart_subtotal * Decimal('0.20')).quantize(Decimal('0.01'))
    return Decimal('0.00')

@login_required
def checkout_view(request):
    user_is_seller = hasattr(request.user, 'profile') and request.user.profile.is_seller
    if request.user.is_staff or user_is_seller:
        role_label = "Admin" if request.user.is_staff else "Brand Merchant"
        messages.warning(request, f"{role_label} Viewer Mode: {role_label} accounts cannot proceed to checkout or place orders.")
        return redirect('products:list')

    cart = get_or_create_cart(request)
    if cart.total_items == 0:
        messages.warning(request, "Your cart is empty! Add headsets to your cart before checking out.")
        return redirect('cart:detail')

    addresses = ShippingAddress.objects.filter(user=request.user)
    discount = _get_discount_from_session(request, cart.subtotal)
    total_amount = max(Decimal('0.00'), cart.grand_total - discount)

    # Clear any previously typed shipping session info so address inputs start clean
    request.session.pop('shipping_info', None)

    # Automatically fetch saved user full name and phone number from account profile
    user_full_name = request.user.get_full_name().strip()
    if not user_full_name:
        user_full_name = (request.user.first_name.strip() or request.user.username).strip()

    user_phone = ''
    if hasattr(request.user, 'profile') and request.user.profile.phone:
        user_phone = request.user.profile.phone.strip()
    elif addresses.exists():
        default_addr = addresses.filter(is_default=True).first() or addresses.first()
        user_phone = default_addr.phone_number

    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'addresses': addresses,
        'discount': discount,
        'total_amount': total_amount,
        'default_full_name': user_full_name,
        'default_phone': user_phone,
    })

@login_required
def payment_gateway_view(request):
    user_is_seller = hasattr(request.user, 'profile') and request.user.profile.is_seller
    if request.user.is_staff or user_is_seller:
        role_label = "Admin" if request.user.is_staff else "Brand Merchant"
        messages.warning(request, f"{role_label} Viewer Mode: {role_label} accounts cannot process payments.")
        return redirect('products:list')

    if request.method != 'POST':
        return redirect('orders:checkout')

    cart = get_or_create_cart(request)
    if cart.total_items == 0:
        return redirect('cart:detail')

    # Save shipping info into session for payment step
    address_id = request.POST.get('address_id')
    if address_id:
        addr = get_object_or_404(ShippingAddress, id=address_id, user=request.user)
        shipping_info = {
            'full_name': addr.full_name,
            'phone': addr.phone_number,
            'email': request.user.email,
            'street_address': addr.street_address,
            'apartment_address': addr.apartment_address or '',
            'city': addr.city,
            'state': addr.state,
            'postal_code': addr.postal_code,
            'country': addr.country
        }
    else:
        full_name = request.POST.get('full_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        street_address = request.POST.get('street_address', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        postal_code = request.POST.get('postal_code', '').strip()

        # Strict validation: all shipping fields are mandatory
        missing_fields = []
        if not full_name:
            missing_fields.append("Full Name")
        if not phone:
            missing_fields.append("Phone Number")
        if not street_address:
            missing_fields.append("Street Address")
        if not city:
            missing_fields.append("City")
        if not state:
            missing_fields.append("State")
        if not postal_code:
            missing_fields.append("Postal Code")

        if missing_fields:
            messages.error(request, f"Please fill in all required fields: {', '.join(missing_fields)}.")
            return redirect('orders:checkout')

        shipping_info = {
            'full_name': full_name,
            'phone': phone,
            'email': request.user.email,
            'street_address': street_address,
            'apartment_address': request.POST.get('apartment_address', '').strip(),
            'city': city,
            'state': state,
            'postal_code': postal_code,
            'country': request.POST.get('country', 'India')
        }

        # Optional: Save address for subsequent checkouts
        if request.POST.get('save_address') == '1':
            ShippingAddress.objects.create(
                user=request.user,
                full_name=full_name,
                phone_number=phone,
                street_address=street_address,
                apartment_address=shipping_info['apartment_address'],
                city=city,
                state=state,
                postal_code=postal_code,
                country=shipping_info['country'],
                is_default=(not ShippingAddress.objects.filter(user=request.user).exists())
            )

        # Update profile phone if not present
        if hasattr(request.user, 'profile') and not request.user.profile.phone and phone:
            request.user.profile.phone = phone
            request.user.profile.save()

    request.session['shipping_info'] = shipping_info
    discount = _get_discount_from_session(request, cart.subtotal)
    total_amount = max(Decimal('0.00'), cart.grand_total - discount)

    return render(request, 'orders/payment.html', {
        'cart': cart,
        'shipping_info': shipping_info,
        'discount': discount,
        'total_amount': total_amount,
    })

@login_required
def process_payment_view(request):
    if request.method != 'POST':
        return redirect('orders:checkout')

    cart = get_or_create_cart(request)
    if cart.total_items == 0:
        messages.error(request, "Session expired or cart is empty.")
        return redirect('cart:detail')

    shipping_info = request.session.get('shipping_info', None)
    if not shipping_info:
        messages.error(request, "Shipping information missing. Please re-enter shipping details.")
        return redirect('orders:checkout')

    payment_method = request.POST.get('payment_method', 'card')

    discount = _get_discount_from_session(request, cart.subtotal)
    subtotal = cart.subtotal
    tax = cart.tax
    shipping = cart.shipping
    total_amount = max(Decimal('0.00'), cart.grand_total - discount)

    with transaction.atomic():
        # 1. Create Order
        order = Order.objects.create(
            user=request.user,
            full_name=shipping_info['full_name'],
            email=shipping_info['email'],
            phone=shipping_info['phone'],
            street_address=shipping_info['street_address'],
            apartment_address=shipping_info['apartment_address'],
            city=shipping_info['city'],
            state=shipping_info['state'],
            postal_code=shipping_info['postal_code'],
            country=shipping_info['country'],
            subtotal=subtotal,
            tax=tax,
            shipping=shipping,
            discount=discount,
            total_amount=total_amount,
            status='Processing',
            payment_status='Paid' if payment_method != 'cod' else 'Unpaid'
        )

        # 2. Create OrderItems & atomically deduct inventory stock with row locking
        for cart_item in cart.items.select_related('product').all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                product_name=cart_item.product.name,
                price=cart_item.product.current_price,
                quantity=cart_item.quantity
            )
            # Atomic row locking & stock reduction
            locked_prod = Product.objects.select_for_update().get(id=cart_item.product.id)
            if locked_prod.stock >= cart_item.quantity:
                locked_prod.stock = F('stock') - cart_item.quantity
                locked_prod.save(update_fields=['stock'])
            else:
                messages.warning(request, f"Product '{locked_prod.name}' was low on stock during checkout.")

        # 3. Create Payment Record
        txn_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        Payment.objects.create(
            order=order,
            payment_method=payment_method,
            transaction_id=txn_id,
            amount=total_amount,
            status='Success'
        )

        # 4. Clear cart & clean session
        cart.items.all().delete()
        request.session.pop('shipping_info', None)
        request.session.pop('coupon_code', None)

        # 5. Create Order Notification for User
        from notifications.models import Notification
        Notification.objects.create(
            user=request.user,
            title="Order Placed Successfully",
            message=f"Your SoundSphere order #{order.order_number} has been placed successfully!",
            notification_type="order",
            link=f"/orders/detail/{order.order_number}/"
        )
        for admin_user in User.objects.filter(is_staff=True):
            Notification.objects.create(
                user=admin_user,
                title="New Order Received 🛒",
                message=f"Order #{order.order_number} (${order.total_amount}) placed by {order.full_name} (@{request.user.username}).",
                notification_type="order",
                link="/admin-panel/orders/"
            )

        # 6. Dispatch Email Confirmation to Customer
        try:
            email_subject = f"SoundSphere Order Confirmation - #{order.order_number}"
            email_message = (
                f"Dear {order.full_name},\n\n"
                f"Thank you for your purchase on SoundSphere!\n\n"
                f"Order Number: #{order.order_number}\n"
                f"Total Amount: ${order.total_amount}\n"
                f"Payment Status: {order.payment_status}\n"
                f"Delivery Address: {order.street_address}, {order.city}, {order.state} {order.postal_code}\n\n"
                f"You can track your order status live at any time on your SoundSphere account dashboard.\n\n"
                f"Best regards,\n"
                f"SoundSphere Audio Team"
            )
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@soundsphere.com')
            send_mail(email_subject, email_message, from_email, [order.email], fail_silently=True)
        except (BadHeaderError, smtplib.SMTPException, OSError) as e:
            logger.warning("Failed to send order confirmation email: %s", e)

    messages.success(request, f"Order #{order.order_number} placed successfully!")
    return redirect('orders:confirmation', order_number=order.order_number)

@login_required
def order_confirmation_view(request, order_number):
    order = get_object_or_404(Order.objects.prefetch_related('items__product'), order_number=order_number, user=request.user)
    return render(request, 'orders/confirmation.html', {'order': order})

@login_required
def order_history_view(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items__product').order_by('-created_at')
    return render(request, 'orders/my_orders.html', {'orders': orders})

@login_required
def order_detail_view(request, order_number):
    order = get_object_or_404(
        Order.objects.prefetch_related('items__product__seller').select_related('payment'),
        order_number=order_number,
        user=request.user
    )
    return render(request, 'orders/order_detail.html', {'order': order})

@login_required
def cancel_order_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    if order.status == 'Delivered':
        messages.error(request, f"Order #{order.order_number} has already been delivered and cannot be cancelled. You may request a return within 7 days.")
        return redirect('orders:detail', order_number=order_number)

    if order.status == 'Cancelled':
        messages.info(request, f"Order #{order.order_number} is already cancelled.")
        return redirect('orders:detail', order_number=order_number)

    if order.is_cancellable:
        reason = request.POST.get('reason', 'Customer requested cancellation') if request.method == 'POST' else 'Customer requested cancellation'
        order.status = 'Cancelled'

        # Restore product inventory stock atomically
        for item in order.items.all():
            if item.product_id:
                Product.objects.filter(id=item.product_id).update(stock=F('stock') + item.quantity)

        # Check if order was paid online
        is_online_paid = (order.payment_status == 'Paid') or (hasattr(order, 'payment') and order.payment.payment_method != 'cod')

        from notifications.models import Notification
        if is_online_paid:
            order.payment_status = 'Refund Initiated'
            order.save()

            Notification.objects.create(
                user=request.user,
                title=f"Order #{order.order_number} Cancelled - Refund Initiated",
                message=f"Your order #{order.order_number} has been cancelled ({reason}). A refund of ₹{order.total_amount} will be credited to your original payment method within 24 hours.",
                notification_type="order",
                link=f"/orders/detail/{order.order_number}/"
            )
            messages.success(
                request,
                f"Order #{order.order_number} has been cancelled successfully. Your refund of ₹{order.total_amount} has been initiated and will be credited to your original payment method within 24 hours."
            )
        else:
            order.save()
            Notification.objects.create(
                user=request.user,
                title=f"Order #{order.order_number} Cancelled",
                message=f"Your order #{order.order_number} has been cancelled successfully.",
                notification_type="order",
                link=f"/orders/detail/{order.order_number}/"
            )
            messages.success(request, f"Order #{order.order_number} has been cancelled successfully.")
    else:
        messages.error(request, f"Order #{order.order_number} cannot be cancelled as it is currently '{order.status}'.")

    return redirect('orders:detail', order_number=order_number)

@login_required
def download_invoice_view(request, order_number):
    order = get_object_or_404(Order.objects.prefetch_related('items__product'), order_number=order_number, user=request.user)
    return render(request, 'orders/invoice.html', {'order': order})


