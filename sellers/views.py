from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import SellerProfile
from notifications.models import Notification
from orders.models import Order, OrderItem
from products.models import Category, Product

from .decorators import seller_approved_required, seller_required


def seller_register_view(request):
    return redirect('/accounts/register/?role=seller')

def seller_login_view(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'profile') and request.user.profile.is_seller:
            return redirect('sellers:dashboard')
        elif request.user.is_staff or request.user.is_superuser:
            return redirect('admin_panel:dashboard')
        return redirect('products:home')

    if request.method == 'POST':
        login_input = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user_obj = User.objects.filter(Q(email__iexact=login_input) | Q(username__iexact=login_input)).first()
        target_username = user_obj.username if user_obj else login_input

        user = authenticate(username=target_username, password=password)
        if user:
            user_is_seller = (hasattr(user, 'profile') and user.profile.is_seller) or hasattr(user, 'seller_profile')
            user_is_admin = user.is_staff or user.is_superuser
            if user_is_seller or user_is_admin:
                login(request, user)
                if user_is_admin:
                    return redirect('admin_panel:dashboard')
                store_name = user.seller_profile.store_name if hasattr(user, 'seller_profile') else user.username
                messages.success(request, f"Welcome back, {store_name}!")
                return redirect('sellers:dashboard')
            else:
                messages.error(request, "Access restricted. This account is registered as a Customer. Please log in through Customer login.")
                return render(request, 'sellers/login.html', {'login_input': login_input})
        else:
            messages.error(request, "Invalid email address or password for Seller login.")
            return render(request, 'sellers/login.html', {'login_input': login_input})
    return render(request, 'sellers/login.html')

@seller_required
def seller_dashboard_view(request):
    seller_profile = getattr(request.user, 'seller_profile', None)
    seller_products = Product.objects.filter(seller=seller_profile) if seller_profile else Product.objects.none()
    total_products = seller_products.count()
    
    seller_order_items = OrderItem.objects.filter(product__seller=seller_profile, order__payment_status='Paid') if seller_profile else OrderItem.objects.none()
    total_revenue = sum(item.total_price for item in seller_order_items)
    items_sold = sum(item.quantity for item in seller_order_items)
    
    low_stock = seller_products.filter(stock__lte=5)
    recent_items = seller_order_items.select_related('order', 'product').order_by('-order__created_at')[:6]
    is_approved = seller_profile.is_approved if seller_profile else False

    return render(request, 'sellers/dashboard.html', {
        'total_products': total_products,
        'total_revenue': total_revenue,
        'items_sold': items_sold,
        'low_stock': low_stock,
        'recent_items': recent_items,
        'is_approved': is_approved,
        'seller_profile': seller_profile,
        'store_name': seller_profile.store_name if seller_profile else request.user.username
    })

@seller_required
def seller_reapply_view(request):
    seller_profile = getattr(request.user, 'seller_profile', None)
    if not seller_profile:
        messages.error(request, "No seller profile found. Please register as a seller first.")
        return redirect('sellers:register')

    if seller_profile.is_approved:
        messages.info(request, "Your seller account is already approved! You can manage your catalog directly.")
        return redirect('sellers:dashboard')

    if request.method == 'POST':
        store_name = request.POST.get('store_name', '').strip()
        tagline = request.POST.get('tagline', '').strip()
        store_description = request.POST.get('store_description', '').strip()
        phone = request.POST.get('phone', '').strip()
        tax_id = request.POST.get('tax_id', '').strip()
        location = request.POST.get('location', '').strip()
        state = request.POST.get('state', '').strip()
        reapplication_notes = request.POST.get('reapplication_notes', '').strip()
        logo_file = request.FILES.get('logo')
        compliance_agreed = request.POST.get('compliance_agreed') == 'on'

        errors = []
        if not store_name:
            errors.append("Brand / Store Name is required.")
        elif SellerProfile.objects.filter(store_name__iexact=store_name).exclude(pk=seller_profile.pk).exists():
            errors.append(f"A brand with the name '{store_name}' already exists. Please choose a unique name.")

        if not phone:
            errors.append("Valid contact phone number is required.")
        if not tax_id:
            errors.append("Business ID / Tax ID is required for verification.")
        if not location or not state:
            errors.append("Store location (City and State) is required.")
        if not store_description or len(store_description.split()) < 5:
            errors.append("Please provide a comprehensive Brand Description explaining your audio gear.")
        if not compliance_agreed:
            errors.append("You must agree to the SoundSphere Seller Quality & Authenticity Guidelines.")
        if seller_profile.status == 'rejected' and not reapplication_notes:
            errors.append("Please provide a brief note explaining the corrections made for this reapplication.")

        if errors:
            for err in errors:
                messages.error(request, err)
            return render(request, 'sellers/reapply.html', {
                'seller_profile': seller_profile,
                'form_data': request.POST,
            })

        seller_profile.store_name = store_name
        seller_profile.tagline = tagline or None
        seller_profile.store_description = store_description
        seller_profile.phone = phone
        seller_profile.tax_id = tax_id
        seller_profile.location = location
        seller_profile.state = state
        if logo_file:
            seller_profile.logo = logo_file

        seller_profile.reapplication_notes = reapplication_notes
        seller_profile.reapplication_count += 1
        seller_profile.reapplied_at = timezone.now()
        seller_profile.has_reapplied = True
        seller_profile.status = 'pending'
        seller_profile.save()

        # Notify admin staff
        for admin_user in User.objects.filter(is_staff=True):
            Notification.objects.create(
                user=admin_user,
                title="Seller Application Resubmitted 📋",
                message=f"Brand '{seller_profile.store_name}' ({seller_profile.user.username}) has reapplied for seller approval (Attempt #{seller_profile.reapplication_count + 1}).",
                notification_type="seller",
                link="/admin-panel/sellers/moderation/"
            )

        # Notify seller
        Notification.objects.create(
            user=request.user,
            title="Reapplication Submitted ⏳",
            message=f"Your updated brand application for '{seller_profile.store_name}' (Attempt #{seller_profile.reapplication_count + 1}) is now under Admin review.",
            notification_type="seller",
            link="/sellers/dashboard/"
        )

        messages.success(
            request,
            f"Your application for '{seller_profile.store_name}' has been updated and resubmitted (Attempt #{seller_profile.reapplication_count + 1}). SoundSphere admins will review it promptly."
        )
        return redirect('sellers:dashboard')

    return render(request, 'sellers/reapply.html', {
        'seller_profile': seller_profile
    })

@seller_required
def seller_products_view(request):
    seller_profile = getattr(request.user, 'seller_profile', None)
    products = Product.objects.filter(seller=seller_profile) if seller_profile else Product.objects.none()
    is_approved = seller_profile.is_approved if seller_profile else False
    return render(request, 'sellers/products_list.html', {
        'products': products,
        'is_approved': is_approved
    })

DEFAULT_CATEGORIES = [
    ("Wireless Headphones", "Over-ear and on-ear wireless Bluetooth headphones", False),
    ("Gaming Headphones", "Headphones optimized for gaming", False),
    ("Noise Cancelling Headphones", "Headphones with active noise cancellation", False),
    ("Headphones", "Standard wired and wireless headphones", False),
    ("Headsets", "Headphones with integrated microphones for communication", False),
]

def ensure_default_categories():
    if Category.objects.count() == 0:
        for name, desc, is_acc in DEFAULT_CATEGORIES:
            Category.objects.get_or_create(name=name, defaults={'description': desc, 'is_accessory': is_acc})

@seller_approved_required
def seller_add_product_view(request):
    ensure_default_categories()
    categories = Category.objects.all()
    seller_profile = getattr(request.user, 'seller_profile', None)

    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        new_category_name = request.POST.get('new_category', '').strip()

        price = request.POST.get('price')
        discount_price = request.POST.get('discount_price') or None
        description = request.POST.get('description')
        stock = request.POST.get('stock', 10)
        image_file = request.FILES.get('image')

        # Dynamic Category Selection / Creation
        if new_category_name:
            category, _ = Category.objects.get_or_create(name=new_category_name)
        elif category_id:
            category = get_object_or_404(Category, id=category_id)
        else:
            messages.error(request, "Please select or type a Product Category.")
            return redirect('sellers:add_product')

        approval_status = 'approved'

        product = Product.objects.create(
            seller=seller_profile,
            name=name,
            category=category,
            price=price,
            discount_price=discount_price,
            description=description,
            stock=stock,
            image=image_file,
            approval_status=approval_status,
            rejection_reason=None,
            driver_size=request.POST.get('driver_size', '').strip() or None,
            battery_life=request.POST.get('battery_life', '').strip() or None,
            connectivity=request.POST.get('connectivity', '').strip() or None,
            noise_cancellation=request.POST.get('noise_cancellation', '').strip() or None,
            frequency_response=request.POST.get('frequency_response', '').strip() or None,
            impedance=request.POST.get('impedance', '').strip() or None,
            weight=request.POST.get('weight', '').strip() or None,
            warranty=request.POST.get('warranty', '').strip() or None
        )

        messages.success(request, f"Product '{product.name}' listed successfully!")
        return redirect('sellers:products')

    return render(request, 'sellers/product_form.html', {
        'categories': categories,
        'action': 'List New'
    })

@seller_approved_required
def seller_edit_product_view(request, product_id):
    ensure_default_categories()
    seller_profile = getattr(request.user, 'seller_profile', None)
    product = get_object_or_404(Product, id=product_id, seller=seller_profile)
    categories = Category.objects.all()

    if request.method == 'POST':
        product.name = request.POST.get('name')
        
        category_id = request.POST.get('category')
        new_category_name = request.POST.get('new_category', '').strip()
        if new_category_name:
            cat, _ = Category.objects.get_or_create(name=new_category_name)
            product.category = cat
        elif category_id:
            product.category_id = category_id

        product.price = request.POST.get('price')
        product.discount_price = request.POST.get('discount_price') or None
        product.description = request.POST.get('description')
        product.stock = request.POST.get('stock')
        if request.FILES.get('image'):
            product.image = request.FILES.get('image')
        
        product.driver_size = request.POST.get('driver_size', '').strip() or None
        product.battery_life = request.POST.get('battery_life', '').strip() or None
        product.connectivity = request.POST.get('connectivity', '').strip() or None
        product.noise_cancellation = request.POST.get('noise_cancellation', '').strip() or None
        product.frequency_response = request.POST.get('frequency_response', '').strip() or None
        product.impedance = request.POST.get('impedance', '').strip() or None
        product.weight = request.POST.get('weight', '').strip() or None
        product.warranty = request.POST.get('warranty', '').strip() or None
        product.save()

        messages.success(request, f"Updated product '{product.name}' details successfully.")
        return redirect('sellers:products')

    return render(request, 'sellers/product_form.html', {
        'product': product,
        'categories': categories,
        'action': 'Edit'
    })

@seller_approved_required
def seller_delete_product_view(request, product_id):
    seller_profile = getattr(request.user, 'seller_profile', None)
    product = get_object_or_404(Product, id=product_id, seller=seller_profile)
    name = product.name
    product.delete()
    messages.success(request, f"Removed product '{name}' from database.")
    return redirect('sellers:products')

@seller_required
def seller_orders_view(request):
    seller_profile = getattr(request.user, 'seller_profile', None)
    seller_order_items = OrderItem.objects.filter(product__seller=seller_profile).select_related('order', 'product') if seller_profile else OrderItem.objects.none()
    
    # Extract unique orders for this seller
    orders_dict = {}
    for item in seller_order_items:
        if item.order.pk not in orders_dict:
            orders_dict[item.order.pk] = {
                'order': item.order,
                'items': []
            }
        orders_dict[item.order.pk]['items'].append(item)
        
    return render(request, 'sellers/orders_list.html', {
        'orders_list': orders_dict.values(),
        'order_items': seller_order_items,
        'status_choices': Order.STATUS_CHOICES
    })

@seller_approved_required
def update_seller_order_status_view(request, order_number):
    seller_profile = getattr(request.user, 'seller_profile', None)
    if not seller_profile:
        messages.error(request, "Seller profile required.")
        return redirect('sellers:dashboard')
        
    has_seller_item = OrderItem.objects.filter(order_id=order_number, product__seller=seller_profile).exists()
    if not has_seller_item:
        messages.error(request, "Permission denied: Order does not contain products from your brand.")
        return redirect('sellers:orders')
        
    order = get_object_or_404(Order, order_number=order_number)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            if order.user:
                Notification.objects.create(
                    user=order.user,
                    title=f"Order #{order.order_number} Update from {seller_profile.store_name}",
                    message=f"Your order #{order.order_number} status has been updated to '{new_status}' by {seller_profile.store_name}.",
                    notification_type="order",
                    link=f"/orders/detail/{order.order_number}/"
                )
            messages.success(request, f"Order #{order.order_number} status updated to '{new_status}'.")
    return redirect('sellers:orders')

