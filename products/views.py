from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Avg, Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import Category, Product, Review


def home_view(request):
    featured_products = list(
        Product.objects.select_related('category')
        .filter(is_featured=True, is_active=True, approval_status='approved')
        .annotate(avg_rating=Avg('reviews__rating'), total_reviews=Count('reviews'))[:8]
    )
    if not featured_products:
        featured_products = list(
            Product.objects.select_related('category')
            .filter(is_active=True, approval_status='approved')
            .annotate(avg_rating=Avg('reviews__rating'), total_reviews=Count('reviews'))[:8]
        )

    headphone_categories = Category.objects.filter(is_accessory=False).annotate(
        product_count=Count('products', filter=Q(products__is_active=True, products__approval_status='approved'))
    )
    
    from accounts.models import CustomerFeedback
    recent_feedback = list(CustomerFeedback.objects.all()[:4])

    return render(request, 'home.html', {
        'featured_products': featured_products,
        'headphone_categories': headphone_categories,
        'recent_feedback': recent_feedback,
    })

def product_list_view(request):
    products = Product.objects.select_related('category', 'seller').filter(is_active=True, approval_status='approved')
    
    # Category Filter
    category_slug = request.GET.get('category')
    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=selected_category)

    # Search Query
    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) | 
            Q(seller__store_name__icontains=query) |
            Q(category__name__icontains=query)
        )

    # Type Filter (headphone vs accessory)
    product_type = request.GET.get('type')
    if product_type == 'headphone':
        products = products.filter(category__is_accessory=False)
    elif product_type == 'accessory':
        products = products.filter(category__is_accessory=True)

    # Price Range Filter
    price_range = request.GET.get('price_range')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if price_range == 'under_15000':
        products = products.filter(price__lt=15000)
    elif price_range == '15000_25000':
        products = products.filter(price__gte=15000, price__lte=25000)
    elif price_range == 'above_25000':
        products = products.filter(price__gt=25000)
    elif min_price or max_price:
        if min_price:
            products = products.filter(price__gte=min_price)
        if max_price:
            products = products.filter(price__lte=max_price)

    # In Stock Filter
    in_stock = request.GET.get('in_stock')
    if in_stock == '1':
        products = products.filter(stock__gt=0)

    # Rating Filter (1-5 stars)
    min_rating = request.GET.get('min_rating')
    if min_rating:
        products = products.filter(reviews__rating__gte=int(min_rating)).distinct()

    # Sorting
    sort = request.GET.get('sort', 'featured')
    if sort == 'price_low':
        products = products.order_by('price')
    elif sort == 'price_high':
        products = products.order_by('-price')
    elif sort == 'rating':
        products = products.annotate(avg_r=Avg('reviews__rating')).order_by('-avg_r', '-created_at')
    elif sort == 'newest':
        products = products.order_by('-created_at')
    else:
        products = products.order_by('-is_featured', '-created_at')

    total_count = products.count()

    # Pagination: 9 items per page
    paginator = Paginator(products, 9)
    page = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    categories = Category.objects.annotate(
        active_count=Count('products', filter=Q(products__is_active=True, products__approval_status='approved'))
    )

    return render(request, 'products/list.html', {
        'products': page_obj,
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': selected_category,
        'query': query,
        'sort': sort,
        'product_type': product_type,
        'min_price': min_price,
        'max_price': max_price,
        'price_range': price_range,
        'in_stock': in_stock,
        'min_rating': min_rating,
        'total_count': total_count,
    })

def product_detail_view(request, slug):
    product = get_object_or_404(Product.objects.select_related('category', 'seller'), slug=slug, is_active=True, approval_status='approved')
    related_products = Product.objects.select_related('category').filter(
        category=product.category, is_active=True, approval_status='approved'
    ).exclude(id=product.id)[:4]

    reviews = product.reviews.select_related('user').all()
    total_reviews = reviews.count()
    rating_counts = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    for r in reviews:
        if r.rating in rating_counts:
            rating_counts[r.rating] += 1

    rating_breakdown = []
    for star in [5, 4, 3, 2, 1]:
        cnt = rating_counts[star]
        pct = int((cnt / total_reviews * 100)) if total_reviews > 0 else 0
        rating_breakdown.append({
            'stars': star,
            'count': cnt,
            'pct': pct,
        })

    # Manage Recently Viewed Products in Session
    recently_viewed_ids = request.session.get('recently_viewed', [])
    if product.id in recently_viewed_ids:
        recently_viewed_ids.remove(product.id)
    recently_viewed_ids.insert(0, product.id)
    request.session['recently_viewed'] = recently_viewed_ids[:6]

    recently_viewed_products = Product.objects.filter(id__in=recently_viewed_ids, is_active=True, approval_status='approved').exclude(id=product.id)[:4]

    return render(request, 'products/detail.html', {
        'product': product,
        'related_products': related_products,
        'recently_viewed_products': recently_viewed_products,
        'reviews': reviews,
        'rating_breakdown': rating_breakdown,
        'total_reviews': total_reviews,
    })


@login_required
def add_review_view(request, slug):
    product = get_object_or_404(Product, slug=slug)
    if request.method == 'POST':
        rating = request.POST.get('rating', 5)
        headline = request.POST.get('headline', '')
        comment = request.POST.get('comment', '')

        Review.objects.create(
            product=product,
            user=request.user,
            rating=int(rating),
            headline=headline,
            comment=comment
        )
        messages.success(request, "Thank you for submitting your review!")
    return redirect('products:detail', slug=slug)

def search_suggestions_view(request):
    query = request.GET.get('q', '').strip()
    results = []
    if len(query) >= 2:
        products = Product.objects.select_related('category', 'seller').filter(
            Q(name__icontains=query) | Q(seller__store_name__icontains=query) | Q(category__name__icontains=query)
        ).filter(is_active=True, approval_status='approved')[:8]
        
        for p in products:
            results.append({
                'name': p.name,
                'slug': p.slug,
                'price': str(p.current_price),
                'image': p.image.url if p.image else '',
                'category': p.category.name,
            })
    return JsonResponse({'results': results})

