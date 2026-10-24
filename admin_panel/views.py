from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import CustomerFeedback, SellerProfile, UserProfile
from notifications.models import Notification
from orders.models import Order
from products.models import Category, Product


def get_admin_common_context():
    return {
        'pending_sellers_count': SellerProfile.objects.filter(status='pending').count(),
        'pending_products_count': Product.objects.filter(approval_status='pending').count(),
    }

@staff_member_required
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

@staff_member_required
def manage_products_view(request):
    products = Product.objects.all().select_related('category', 'seller', 'seller__user').order_by('-created_at')
    ctx = get_admin_common_context()
    ctx['products'] = products
    return render(request, 'admin_panel/products_list.html', ctx)

@staff_member_required
def add_product_view(request):
    messages.error(request, "Admins cannot add products directly. Only approved brand sellers can add products to the catalog.")
    return redirect('admin_panel:products')

@staff_member_required
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

@staff_member_required
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

@staff_member_required
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

@staff_member_required
def manage_orders_view(request):
    orders = Order.objects.all().select_related('user').order_by('-created_at')
    ctx = get_admin_common_context()
    ctx['orders'] = orders
    return render(request, 'admin_panel/orders_list.html', ctx)

@staff_member_required
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

@staff_member_required
def product_moderation_view(request):
    pending_products = Product.objects.filter(approval_status='pending').select_related('seller', 'category')
    ctx = get_admin_common_context()
    ctx['products'] = pending_products
    return render(request, 'admin_panel/moderation.html', ctx)

@staff_member_required
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

@staff_member_required
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

@staff_member_required
def seller_moderation_view(request):
    pending_sellers = SellerProfile.objects.filter(status='pending').select_related('user').order_by('-reapplied_at', '-created_at')
    approved_sellers = SellerProfile.objects.filter(status='approved').select_related('user').order_by('-created_at')
    rejected_sellers = SellerProfile.objects.filter(Q(status='rejected') | Q(has_reapplied=True)).select_related('user').distinct().order_by('-updated_at')

    active_tab = request.GET.get('tab', 'pending')
    ctx = get_admin_common_context()
    ctx.update({
        'pending_sellers': pending_sellers,
        'approved_sellers': approved_sellers,
        'rejected_sellers': rejected_sellers,
        'pending_count': pending_sellers.count(),
        'approved_count': approved_sellers.count(),
        'rejected_count': rejected_sellers.count(),
        'active_tab': active_tab,
    })
    return render(request, 'admin_panel/seller_moderation.html', ctx)

@staff_member_required
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

@staff_member_required
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
@staff_member_required
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
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(seller_profile__store_name__icontains=search_query)
        )

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

@staff_member_required
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

@staff_member_required
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
@staff_member_required
def feedback_moderation_view(request):
    feedbacks = CustomerFeedback.objects.all().order_by('-created_at')
    ctx = get_admin_common_context()
    ctx['feedbacks'] = feedbacks
    return render(request, 'admin_panel/feedback_list.html', ctx)

@staff_member_required
def delete_feedback_view(request, feedback_id):
    feedback = get_object_or_404(CustomerFeedback, id=feedback_id)
    feedback.delete()
    messages.success(request, "Customer feedback entry deleted.")
    return redirect('admin_panel:feedback_moderation')



