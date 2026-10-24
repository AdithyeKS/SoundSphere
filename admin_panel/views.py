import csv
import json
from datetime import datetime, timedelta
from decimal import Decimal

from functools import wraps

from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Avg, Count, F, Q, Sum
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone


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

from accounts.models import CustomerFeedback, SellerProfile, UserProfile
from notifications.models import Notification
from orders.models import Order, OrderItem, Payment
from products.models import Category, Product


def get_admin_common_context():
    return {
        'pending_sellers_count': SellerProfile.objects.filter(status='pending').count(),
        'pending_products_count': Product.objects.filter(approval_status='pending').count(),
    }

@admin_required
def dashboard_view(request):
    # Ensure profile role consistency
    all_users = User.objects.all().select_related('profile', 'seller_profile')
    for u in all_users:
        prof, _ = UserProfile.objects.get_or_create(user=u)
        if (u.is_staff or u.is_superuser) and prof.role != 'admin':
            prof.role = 'admin'
            prof.save()
        elif hasattr(u, 'seller_profile') and prof.role != 'seller':
            prof.role = 'seller'
            prof.save()

    total_users = User.objects.count()
    total_admins = User.objects.filter(Q(is_staff=True) | Q(is_superuser=True) | Q(profile__role='admin')).distinct().count()
    total_sellers = User.objects.filter(Q(seller_profile__isnull=False) | Q(profile__role='seller')).exclude(Q(is_staff=True) | Q(is_superuser=True) | Q(profile__role='admin')).distinct().count()
    total_customers = User.objects.exclude(Q(is_staff=True) | Q(is_superuser=True) | Q(profile__role='admin')).exclude(Q(seller_profile__isnull=False) | Q(profile__role='seller')).distinct().count()

    approved_sellers_count = SellerProfile.objects.filter(status='approved').count()
    total_products = Product.objects.count()
    active_products = Product.objects.filter(is_active=True).count()
    blocked_products = Product.objects.filter(is_active=False).count()
    total_orders = Order.objects.count()
    
    pending_sellers = SellerProfile.objects.filter(status='pending').select_related('user').order_by('-id')[:5]
    pending_products = Product.objects.filter(approval_status='pending').select_related('seller', 'category').order_by('-created_at')[:5]
    recent_users = User.objects.all().select_related('profile').order_by('-date_joined')[:5]
    low_stock_products = Product.objects.filter(stock__lte=5)
    total_feedback_count = CustomerFeedback.objects.count()

    pending_sellers_count = SellerProfile.objects.filter(status='pending').count()
    pending_products_count = Product.objects.filter(approval_status='pending').count()
    total_pending_requests = pending_sellers_count + pending_products_count

    ctx = get_admin_common_context()
    ctx.update({
        'total_users': total_users,
        'total_customers': total_customers,
        'total_sellers': total_sellers,
        'total_admins': total_admins,
        'approved_sellers_count': approved_sellers_count,
        'total_products': total_products,
        'active_products': active_products,
        'blocked_products': blocked_products,
        'total_orders': total_orders,
        'pending_sellers': pending_sellers,
        'pending_products': pending_products,
        'pending_sellers_count': pending_sellers_count,
        'pending_products_count': pending_products_count,
        'total_pending_requests': total_pending_requests,
        'recent_users': recent_users,
        'low_stock_products': low_stock_products,
        'total_feedback_count': total_feedback_count,
    })
    return render(request, 'admin_panel/dashboard.html', ctx)

@admin_required
def manage_products_view(request):
    products = Product.objects.all().select_related('category', 'seller', 'seller__user').order_by('-created_at')
    ctx = get_admin_common_context()
    ctx['products'] = products
    return render(request, 'admin_panel/products_list.html', ctx)

@admin_required
def add_product_view(request):
    messages.error(request, "Admins cannot add products directly. Only approved brand sellers can add products to the catalog.")
    return redirect('admin_panel:products')

@admin_required
def edit_product_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    seller_user = product.seller.user if (product.seller and hasattr(product.seller, 'user')) else product.seller
    if seller_user and seller_user != request.user:
        messages.error(request, f"Admin cannot edit seller-listed products ('{product.name}'). You can only remove items from the catalog.")
        return redirect('admin_panel:products')

    categories = Category.objects.all()
    

    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.category_id = request.POST.get('category')
        product.price = request.POST.get('price')
        product.discount_price = request.POST.get('discount_price') or None
        product.description = request.POST.get('description')
        product.stock = request.POST.get('stock')
        product.is_featured = request.POST.get('is_featured') == 'on'
        if request.FILES.get('image'):
            product.image = request.FILES.get('image')
        
        product.driver_size = request.POST.get('driver_size', product.driver_size)
        product.battery_life = request.POST.get('battery_life', product.battery_life)
        product.connectivity = request.POST.get('connectivity', product.connectivity)
        product.noise_cancellation = request.POST.get('noise_cancellation', product.noise_cancellation)
        product.save()

        messages.success(request, f"Product '{product.name}' updated successfully!")
        return redirect('admin_panel:products')

    ctx = get_admin_common_context()
    ctx.update({'product': product, 'categories': categories,  'action': 'Edit'})
    return render(request, 'admin_panel/product_form.html', ctx)

@admin_required
def delete_product_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    name = product.name
    seller = product.seller
    seller_user = seller.user if (seller and hasattr(seller, 'user')) else seller

    if seller_user and seller_user != request.user:
        Notification.objects.create(
            user=seller_user,
            title="Product Listing Removed by Admin",
            message=f"Your product listing '{name}' has been removed from the SoundSphere catalog by Admin.",
            notification_type="product",
            link="/seller/products/"
        )

    product.delete()
    if seller_user and seller_user != request.user:
        seller_name = seller.store_name if hasattr(seller, 'store_name') else seller_user.username
        messages.success(request, f"Product '{name}' was removed from the store catalog. Seller '{seller_name}' has been sent a notification.")
    else:
        messages.success(request, f"Product '{name}' deleted from store catalog.")
    return redirect('admin_panel:products')

@admin_required
def toggle_product_block_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.is_active = not product.is_active
    product.save()
    
    status_str = "unblocked and live in store" if product.is_active else "blocked and hidden from store"
    
    if product.seller:
        seller_user = product.seller.user if hasattr(product.seller, 'user') else product.seller
        Notification.objects.create(
            user=seller_user,
            title=f"Product Listing {'Unblocked' if product.is_active else 'Blocked'} by Admin",
            message=f"Your product listing '{product.name}' has been {status_str} by Admin.",
            notification_type="product",
            link="/seller/products/"
        )
    
    messages.success(request, f"Product '{product.name}' is now {status_str}.")
    return redirect('admin_panel:products')

@admin_required
def manage_orders_view(request):
    orders = Order.objects.all().select_related('user').order_by('-created_at')
    ctx = get_admin_common_context()
    ctx['orders'] = orders
    return render(request, 'admin_panel/orders_list.html', ctx)

@admin_required
def update_order_status_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            Notification.objects.create(
                user=order.user,
                title=f"Order #{order.order_number} Status Update",
                message=f"Your order #{order.order_number} status has been updated to '{new_status}'.",
                notification_type="order",
                link=f"/orders/detail/{order.order_number}/"
            )
            messages.success(request, f"Order #{order.order_number} status updated to {new_status}.")
    return redirect('admin_panel:orders')

@admin_required
def product_moderation_view(request):
    pending_products = Product.objects.filter(approval_status='pending').select_related('seller', 'category')
    ctx = get_admin_common_context()
    ctx['products'] = pending_products
    return render(request, 'admin_panel/moderation.html', ctx)

@admin_required
def approve_product_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.approval_status = 'approved'
    product.rejection_reason = None
    product.save()

    if product.seller:
        seller_user = product.seller.user if hasattr(product.seller, 'user') else product.seller
        Notification.objects.create(
            user=seller_user,
            title="Product Listing Approved!",
            message=f"Great news! Your product listing '{product.name}' was approved by Admin and is now live in the store.",
            notification_type="product",
            link=f"/products/detail/{product.slug}/"
        )
    messages.success(request, f"Product '{product.name}' approved and published to store!")
    return redirect('admin_panel:moderation')

@admin_required
def reject_product_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        reason = request.POST.get('rejection_reason', 'Listing does not meet quality guidelines.')
        product.approval_status = 'rejected'
        product.rejection_reason = reason
        product.save()

        if product.seller:
            seller_user = product.seller.user if hasattr(product.seller, 'user') else product.seller
            Notification.objects.create(
                user=seller_user,
                title="Product Listing Update Needed",
                message=f"Your product listing '{product.name}' was not approved. Reason: {reason}",
                notification_type="product",
                link="/seller/products/"
            )
        messages.warning(request, f"Product '{product.name}' listing was rejected.")
    return redirect('admin_panel:moderation')

@admin_required
def seller_moderation_view(request):
    search_query = request.GET.get('q', '').strip()
    active_tab = request.GET.get('tab', 'pending')

    pending_sellers = SellerProfile.objects.filter(status='pending').select_related('user').order_by('-reapplied_at', '-created_at')
    approved_sellers = SellerProfile.objects.filter(status='approved').select_related('user').order_by('-created_at')
    rejected_sellers = SellerProfile.objects.filter(Q(status='rejected') | Q(has_reapplied=True)).select_related('user').distinct().order_by('-updated_at')

    if search_query:
        search_filter = (
            Q(store_name__icontains=search_query) |
            Q(tagline__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(tax_id__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        )
        pending_sellers = pending_sellers.filter(search_filter)
        approved_sellers = approved_sellers.filter(search_filter)
        rejected_sellers = rejected_sellers.filter(search_filter)

        # Smart tab selection: if the active tab has 0 matches, switch to one with matches
        if active_tab == 'pending' and not pending_sellers.exists():
            if approved_sellers.exists():
                active_tab = 'approved'
            elif rejected_sellers.exists():
                active_tab = 'rejected'
        elif active_tab == 'approved' and not approved_sellers.exists():
            if pending_sellers.exists():
                active_tab = 'pending'
            elif rejected_sellers.exists():
                active_tab = 'rejected'
        elif active_tab == 'rejected' and not rejected_sellers.exists():
            if approved_sellers.exists():
                active_tab = 'approved'
            elif pending_sellers.exists():
                active_tab = 'pending'

    ctx = get_admin_common_context()
    ctx.update({
        'pending_sellers': pending_sellers,
        'approved_sellers': approved_sellers,
        'rejected_sellers': rejected_sellers,
        'pending_count': pending_sellers.count(),
        'approved_count': approved_sellers.count(),
        'rejected_count': rejected_sellers.count(),
        'active_tab': active_tab,
        'search_query': search_query,
    })
    return render(request, 'admin_panel/seller_moderation.html', ctx)

@admin_required
def approve_seller_view(request, seller_id):
    seller = get_object_or_404(SellerProfile, id=seller_id)
    seller.status = 'approved'
    seller.has_reapplied = False
    seller.rejection_reason = None
    seller.save()

    Notification.objects.create(
        user=seller.user,
        title="Seller Application Approved! 🎉",
        message=f"Congratulations! Your seller store '{seller.store_name}' has been approved by SoundSphere Admin. You can now add and manage audio products in your Seller Dashboard.",
        notification_type="seller",
        link="/sellers/dashboard/"
    )
    messages.success(request, f"Seller store '{seller.store_name}' ({seller.user.username}) approved!")
    return redirect('admin_panel:seller_moderation')

@admin_required
def reject_seller_view(request, seller_id):
    seller = get_object_or_404(SellerProfile, id=seller_id)
    store_name = seller.store_name
    user = seller.user
    reason = request.POST.get('rejection_reason', 'Information or verification details incomplete.')

    seller.status = 'rejected'
    seller.has_reapplied = False
    seller.rejection_reason = reason
    seller.save()

    Notification.objects.create(
        user=user,
        title="Seller Application Notice",
        message=f"Your seller application for '{store_name}' was not approved. Reason: {reason}",
        notification_type="seller",
        link="/sellers/dashboard/"
    )
    messages.warning(request, f"Seller application for '{store_name}' was rejected.")
    return redirect('admin_panel:seller_moderation')

# --- ADMIN USER CONTROL VIEWS ---
@admin_required
def manage_users_view(request):
    role_filter = request.GET.get('role', 'all')
    seller_status = request.GET.get('seller_status', 'all')
    search_query = request.GET.get('q', '').strip()

    all_users = User.objects.all().select_related('profile', 'seller_profile')
    for u in all_users:
        prof, _ = UserProfile.objects.get_or_create(user=u)
        if (u.is_staff or u.is_superuser) and prof.role != 'admin':
            prof.role = 'admin'
            prof.save()
        elif hasattr(u, 'seller_profile') and prof.role != 'seller':
            prof.role = 'seller'
            prof.save()

    # Base counts for tabs
    total_users_count = User.objects.count()
    admins_count = User.objects.filter(Q(is_staff=True) | Q(is_superuser=True) | Q(profile__role='admin')).distinct().count()
    sellers_count = User.objects.filter(Q(seller_profile__isnull=False) | Q(profile__role='seller')).exclude(Q(is_staff=True) | Q(is_superuser=True) | Q(profile__role='admin')).distinct().count()
    customers_count = User.objects.exclude(Q(is_staff=True) | Q(is_superuser=True) | Q(profile__role='admin')).exclude(Q(seller_profile__isnull=False) | Q(profile__role='seller')).distinct().count()

    # Seller application status counts
    pending_sellers_count = SellerProfile.objects.filter(status='pending').count()
    approved_sellers_count = SellerProfile.objects.filter(status='approved').count()
    rejected_sellers_count = SellerProfile.objects.filter(Q(status='rejected') | Q(has_reapplied=True)).distinct().count()

    users = User.objects.all().select_related('profile', 'seller_profile').order_by('-date_joined')

    if search_query:
        search_filter = (
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(profile__phone__icontains=search_query) |
            Q(seller_profile__store_name__icontains=search_query) |
            Q(seller_profile__tagline__icontains=search_query) |
            Q(seller_profile__phone__icontains=search_query) |
            Q(seller_profile__location__icontains=search_query)
        )
        users = users.filter(search_filter)

        # Smart fallback: If a specific role was selected (e.g. customer) but yielded 0 results,
        # check if matching users exist in other roles (e.g. searched brand name 'boAt')
        if role_filter != 'all':
            test_subset = users
            if role_filter == 'customer':
                test_subset = test_subset.filter(profile__role='customer').exclude(is_staff=True).exclude(is_superuser=True).exclude(seller_profile__isnull=False)
            elif role_filter == 'seller':
                test_subset = test_subset.filter(Q(profile__role='seller') | Q(seller_profile__isnull=False))
            elif role_filter == 'admin':
                test_subset = test_subset.filter(Q(is_staff=True) | Q(is_superuser=True) | Q(profile__role='admin'))

            if not test_subset.exists() and users.exists():
                # Matches exist in other roles; switch role_filter to display the found user/brand
                if users.filter(seller_profile__isnull=False).exists():
                    role_filter = 'seller'
                    seller_status = 'all'
                else:
                    role_filter = 'all'

    if role_filter == 'customer':
        users = users.filter(profile__role='customer').exclude(is_staff=True).exclude(is_superuser=True).exclude(seller_profile__isnull=False)
    elif role_filter == 'seller':
        users = users.filter(Q(profile__role='seller') | Q(seller_profile__isnull=False))
        if seller_status == 'pending':
            users = users.filter(seller_profile__status='pending')
        elif seller_status == 'approved':
            users = users.filter(seller_profile__status='approved')
        elif seller_status == 'rejected':
            users = users.filter(Q(seller_profile__status='rejected') | Q(seller_profile__has_reapplied=True))
    elif role_filter == 'admin':
        users = users.filter(Q(is_staff=True) | Q(is_superuser=True) | Q(profile__role='admin'))

    ctx = get_admin_common_context()
    ctx.update({
        'users': users,
        'role_filter': role_filter,
        'seller_status': seller_status,
        'search_query': search_query,
        'total_users_count': total_users_count,
        'customers_count': customers_count,
        'sellers_count': sellers_count,
        'admins_count': admins_count,
        'pending_sellers_count': pending_sellers_count,
        'approved_sellers_count': approved_sellers_count,
        'rejected_sellers_count': rejected_sellers_count,
    })
    return render(request, 'admin_panel/users_list.html', ctx)

@admin_required
def toggle_user_active_view(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    if target_user == request.user:
        messages.error(request, "You cannot deactivate your own active admin account!")
        return redirect('admin_panel:users')

    if target_user.is_staff or target_user.is_superuser or (hasattr(target_user, 'profile') and target_user.profile.role == 'admin'):
        messages.error(request, f"Admin account '{target_user.username}' is protected and cannot be deactivated!")
        return redirect('admin_panel:users')

    target_user.is_active = not target_user.is_active
    target_user.save()
    status_str = "activated" if target_user.is_active else "deactivated"
    messages.success(request, f"User '{target_user.username}' has been {status_str}.")
    return redirect('admin_panel:users')

@admin_required
def delete_user_view(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    if target_user == request.user:
        messages.error(request, "You cannot delete your currently logged in admin account!")
        return redirect('admin_panel:users')

    if target_user.is_staff or target_user.is_superuser or (hasattr(target_user, 'profile') and target_user.profile.role == 'admin'):
        messages.error(request, f"Admin account '{target_user.username}' is protected and cannot be deleted or terminated!")
        return redirect('admin_panel:users')

    username = target_user.username
    target_user.delete()
    messages.success(request, f"User account '{username}' permanently deleted.")
    return redirect('admin_panel:users')

# --- ADMIN CUSTOMER FEEDBACK MODERATION VIEWS ---
@admin_required
def feedback_moderation_view(request):
    feedbacks = CustomerFeedback.objects.all().order_by('-created_at')
    ctx = get_admin_common_context()
    ctx['feedbacks'] = feedbacks
    return render(request, 'admin_panel/feedback_list.html', ctx)

@admin_required
def delete_feedback_view(request, feedback_id):
    feedback = get_object_or_404(CustomerFeedback, id=feedback_id)
    feedback.delete()
    messages.success(request, "Customer feedback entry deleted.")
    return redirect('admin_panel:feedback_moderation')

# --- ADMIN SALES, FINANCIAL & ECOMMERCE ANALYTICS REPORTS ---
@admin_required
def analytics_reports_view(request):
    period = request.GET.get('period', '30d')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    now = timezone.now()
    orders_qs = Order.objects.all().select_related('user', 'payment').prefetch_related('items__product__seller')

    # Date filter
    date_label = "Last 30 Days"
    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
            orders_qs = orders_qs.filter(created_at__gte=start_date, created_at__lt=end_date)
            period = 'custom'
            date_label = f"{start_date_str} to {end_date_str}"
        except ValueError:
            pass
    elif period == 'today':
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        orders_qs = orders_qs.filter(created_at__gte=start_of_day)
        date_label = "Today"
    elif period == '7d':
        orders_qs = orders_qs.filter(created_at__gte=now - timedelta(days=7))
        date_label = "Last 7 Days"
    elif period == '30d':
        orders_qs = orders_qs.filter(created_at__gte=now - timedelta(days=30))
        date_label = "Last 30 Days"
    elif period == 'this_month':
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        orders_qs = orders_qs.filter(created_at__gte=start_of_month)
        date_label = "This Month"
    elif period == 'this_year':
        start_of_year = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        orders_qs = orders_qs.filter(created_at__gte=start_of_year)
        date_label = "This Year"
    elif period == 'all':
        date_label = "All Time"

    # Total Orders
    total_orders = orders_qs.count()

    # Financial calculations
    gross_revenue = orders_qs.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    
    # Realized / Paid Revenue (Paid orders or Delivered orders)
    paid_orders = orders_qs.filter(Q(payment_status='Paid') | Q(status='Delivered'))
    net_revenue = paid_orders.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

    # Platform Profit Estimation:
    # 12% marketplace commission on realized sales
    platform_take_rate = Decimal('0.12')
    estimated_profit = round(net_revenue * platform_take_rate, 2)
    
    # Average Order Value (AOV)
    aov = round((gross_revenue / total_orders), 2) if total_orders > 0 else Decimal('0.00')
    
    total_tax = orders_qs.aggregate(total=Sum('tax'))['total'] or Decimal('0.00')
    total_shipping = orders_qs.aggregate(total=Sum('shipping'))['total'] or Decimal('0.00')
    total_discount = orders_qs.aggregate(total=Sum('discount'))['total'] or Decimal('0.00')

    # Status Breakdown
    delivered_count = orders_qs.filter(status='Delivered').count()
    processing_count = orders_qs.filter(status__in=['Pending', 'Processing', 'Confirmed', 'Packed', 'Shipped', 'Out for Delivery']).count()
    cancelled_count = orders_qs.filter(status='Cancelled').count()
    returned_count = orders_qs.filter(status='Returned').count()

    delivery_rate = round((delivered_count / total_orders * 100), 1) if total_orders > 0 else 0.0
    cancellation_rate = round(((cancelled_count + returned_count) / total_orders * 100), 1) if total_orders > 0 else 0.0

    # Total units sold across these orders
    order_items_qs = OrderItem.objects.filter(order__in=orders_qs).select_related('product__seller', 'order')
    total_units_sold = order_items_qs.aggregate(total=Sum('quantity'))['total'] or 0

    # Brand Performance
    brand_stats = {}
    for item in order_items_qs:
        seller = item.product.seller if item.product and item.product.seller else None
        bname = seller.store_name if seller else 'SoundSphere Direct'
        if bname not in brand_stats:
            brand_stats[bname] = {'units_sold': 0, 'revenue': Decimal('0.00')}
        brand_stats[bname]['units_sold'] += item.quantity
        brand_stats[bname]['revenue'] += (item.price * item.quantity)
    
    brand_performance = []
    for bname, data in brand_stats.items():
        comm = round(data['revenue'] * platform_take_rate, 2)
        brand_performance.append({
            'brand_name': bname,
            'units_sold': data['units_sold'],
            'revenue': data['revenue'],
            'commission': comm,
        })
    brand_performance.sort(key=lambda x: x['revenue'], reverse=True)

    # Top Selling Products
    top_products_dict = {}
    for item in order_items_qs:
        pname = item.product_name
        if pname not in top_products_dict:
            top_products_dict[pname] = {'units': 0, 'revenue': Decimal('0.00')}
        top_products_dict[pname]['units'] += item.quantity
        top_products_dict[pname]['revenue'] += (item.price * item.quantity)
    
    top_products = [
        {'name': k, 'units': v['units'], 'revenue': v['revenue']}
        for k, v in top_products_dict.items()
    ]
    top_products.sort(key=lambda x: x['units'], reverse=True)
    top_products = top_products[:6]

    # Payment Methods Breakdown
    payment_methods_count = {
        'Credit/Debit Card': orders_qs.filter(payment__payment_method='card').count(),
        'UPI / QR Code': orders_qs.filter(payment__payment_method='upi').count(),
        'Net Banking': orders_qs.filter(payment__payment_method='netbanking').count(),
        'Cash on Delivery': orders_qs.filter(payment__payment_method='cod').count(),
    }

    # Daily Timeline for Charts
    daily_aggregates = (
        orders_qs.annotate(order_date=TruncDate('created_at'))
        .values('order_date')
        .annotate(daily_revenue=Sum('total_amount'), daily_orders=Count('order_number'))
        .order_by('order_date')
    )
    chart_dates = [d['order_date'].strftime('%b %d') if d['order_date'] else '' for d in daily_aggregates]
    chart_revenues = [float(d['daily_revenue'] or 0) for d in daily_aggregates]
    chart_orders = [int(d['daily_orders'] or 0) for d in daily_aggregates]

    # Brand chart labels & data (top 6 brands)
    top_brand_labels = [b['brand_name'] for b in brand_performance[:6]]
    top_brand_revenues = [float(b['revenue']) for b in brand_performance[:6]]

    recent_orders = orders_qs.order_by('-created_at')[:50]

    ctx = get_admin_common_context()
    ctx.update({
        'period': period,
        'date_label': date_label,
        'start_date_str': start_date_str or '',
        'end_date_str': end_date_str or '',
        'total_orders': total_orders,
        'gross_revenue': gross_revenue,
        'net_revenue': net_revenue,
        'estimated_profit': estimated_profit,
        'aov': aov,
        'total_tax': total_tax,
        'total_shipping': total_shipping,
        'total_discount': total_discount,
        'total_units_sold': total_units_sold,
        'delivered_count': delivered_count,
        'processing_count': processing_count,
        'cancelled_count': cancelled_count,
        'returned_count': returned_count,
        'delivery_rate': delivery_rate,
        'cancellation_rate': cancellation_rate,
        'brand_performance': brand_performance,
        'top_products': top_products,
        'payment_methods_count': payment_methods_count,
        'recent_orders': recent_orders,
        'chart_dates_json': json.dumps(chart_dates),
        'chart_revenues_json': json.dumps(chart_revenues),
        'chart_orders_json': json.dumps(chart_orders),
        'top_brand_labels_json': json.dumps(top_brand_labels),
        'top_brand_revenues_json': json.dumps(top_brand_revenues),
        'status_counts_json': json.dumps([delivered_count, processing_count, cancelled_count, returned_count]),
        'payment_counts_json': json.dumps(list(payment_methods_count.values())),
        'generated_at': now,
    })
    return render(request, 'admin_panel/reports.html', ctx)

@admin_required
def export_orders_csv_view(request):
    period = request.GET.get('period', 'all')
    now = timezone.now()
    orders_qs = Order.objects.all().select_related('user', 'payment').prefetch_related('items__product__seller').order_by('-created_at')

    if period == 'today':
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        orders_qs = orders_qs.filter(created_at__gte=start_of_day)
    elif period == '7d':
        orders_qs = orders_qs.filter(created_at__gte=now - timedelta(days=7))
    elif period == '30d':
        orders_qs = orders_qs.filter(created_at__gte=now - timedelta(days=30))
    elif period == 'this_month':
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        orders_qs = orders_qs.filter(created_at__gte=start_of_month)
    elif period == 'this_year':
        start_of_year = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        orders_qs = orders_qs.filter(created_at__gte=start_of_year)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="SoundSphere_Orders_Report_{now.strftime("%Y%m%d_%H%M")}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Order Number', 'Date', 'Customer Name', 'Customer Email', 'Customer Phone',
        'Address', 'City', 'State', 'Postal Code', 'Items Count', 'Brands Involved',
        'Subtotal (INR)', 'Tax (INR)', 'Shipping (INR)', 'Discount (INR)', 'Total Amount (INR)',
        'Payment Method', 'Payment Status', 'Order Status'
    ])

    for o in orders_qs:
        pm = o.payment.get_payment_method_display() if hasattr(o, 'payment') and o.payment else 'N/A'
        items = list(o.items.all())
        brands = list(set([it.product.seller.store_name for it in items if it.product and it.product.seller] or ['SoundSphere']))
        brands_str = ", ".join(brands)
        items_count = sum(it.quantity for it in items)

        writer.writerow([
            o.order_number,
            o.created_at.strftime('%Y-%m-%d %H:%M'),
            o.full_name,
            o.email,
            o.phone,
            f"{o.street_address} {o.apartment_address or ''}".strip(),
            o.city,
            o.state,
            o.postal_code,
            items_count,
            brands_str,
            o.subtotal,
            o.tax,
            o.shipping,
            o.discount,
            o.total_amount,
            pm,
            o.payment_status,
            o.status,
        ])
    return response



