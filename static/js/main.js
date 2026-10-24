// SoundSphere Main Client JavaScript

document.addEventListener('DOMContentLoaded', () => {
    initLiveSearch();
    initAjaxCart();
    initAjaxWishlist();
    initDetailTabs();
    initToastAutoDismiss();
});

// Auto-dismiss Django server-side message toasts after 5 seconds
function initToastAutoDismiss() {
    const toasts = document.querySelectorAll('.toast-container .toast');
    toasts.forEach((toast, index) => {
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(-30px) scale(0.92)';
            toast.style.transition = 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
            setTimeout(() => toast.remove(), 400);
        }, 5000 + (index * 200));
    });
}

// Toast notification display helper
function showToast(message, isError = false) {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = 'toast';
    if (isError) {
        toast.style.borderColor = '#ef4444';
        toast.style.boxShadow = '0 15px 40px rgba(239, 68, 68, 0.25), 0 10px 30px rgba(0, 0, 0, 0.8)';
    }
    toast.innerHTML = `
        <div style="display:flex; align-items:center; gap: 0.75rem; justify-content: space-between; width: 100%;">
            <div style="display:flex; align-items:center; gap: 0.75rem;">
                <i class="${isError ? 'bi bi-exclamation-triangle-fill' : 'bi bi-check-circle-fill'}" style="color: ${isError ? '#ef4444' : '#00f2fe'}; font-size: 1.25rem;"></i>
                <span style="font-weight: 600; font-size: 0.95rem;">${message}</span>
            </div>
            <button onclick="this.closest('.toast').remove()" style="background:none; border:none; color:var(--text-muted); cursor:pointer; font-size:1.2rem; line-height:1; margin-left:0.5rem; transition: color 0.2s;" onmouseover="this.style.color='#fff'" onmouseout="this.style.color='var(--text-muted)'">&times;</button>
        </div>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-30px) scale(0.92)';
        toast.style.transition = 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
        setTimeout(() => toast.remove(), 400);
    }, 5000);
}

// Navbar Live Search
function initLiveSearch() {
    const input = document.getElementById('searchInput');
    const dropdown = document.getElementById('searchResults');
    if (!input || !dropdown) return;

    let debounceTimer;
    input.addEventListener('input', (e) => {
        clearTimeout(debounceTimer);
        const query = e.target.value.trim();

        if (query.length < 2) {
            dropdown.style.display = 'none';
            return;
        }

        debounceTimer = setTimeout(() => {
            fetch(`/search-suggestions/?q=${encodeURIComponent(query)}`)
                .then(res => res.json())
                .then(data => {
                    dropdown.innerHTML = '';
                    if (data.results && data.results.length > 0) {
                        data.results.forEach(item => {
                            const a = document.createElement('a');
                            a.href = `/product/${item.slug}/`;
                            a.className = 'search-item';
                            a.innerHTML = `
                                <div>
                                    <div style="font-weight: 600; color: #fff;">${item.name}</div>
                                    <div style="font-size: 0.8rem; color: #00f2fe;">${item.category} • ₹${item.price}</div>
                                </div>
                            `;
                            dropdown.appendChild(a);
                        });
                        dropdown.style.display = 'block';
                    } else {
                        dropdown.innerHTML = '<div style="padding: 0.75rem 1rem; color: #94a3b8; font-size: 0.9rem;">No audio products found</div>';
                        dropdown.style.display = 'block';
                    }
                })
                .catch(() => {
                    dropdown.style.display = 'none';
                });
        }, 250);
    });

    document.addEventListener('click', (e) => {
        if (!input.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.style.display = 'none';
        }
    });
}

// AJAX Add To Cart
function initAjaxCart() {
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('.ajax-add-to-cart');
        if (!btn) return;

        e.preventDefault();
        const productId = btn.dataset.productId;
        const quantityInput = document.getElementById('productQuantity');
        const qty = quantityInput ? quantityInput.value : 1;

        const csrfToken = getCookie('csrftoken');

        fetch(`/cart/add/${productId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: `quantity=${qty}`
        })
        .then(res => res.json())
        .then(data => {
            if (data.require_login) {
                showToast(data.message || "Please log in to add items to your cart.", true);
                setTimeout(() => {
                    window.location.href = data.redirect_url || '/accounts/login/';
                }, 800);
                return;
            }
            if (data.success) {
                showToast(data.message);
                const count = parseInt(data.cart_item_count, 10) || 0;
                let cartBadge = document.getElementById('cartBadgeCount');
                if (!cartBadge) {
                    const navBtn = document.getElementById('cartNavBtn') ||
                                   document.querySelector('a[title="Shopping Cart"]') ||
                                   document.querySelector('a[href*="/cart/"]');
                    if (navBtn) {
                        cartBadge = document.createElement('span');
                        cartBadge.id = 'cartBadgeCount';
                        cartBadge.className = 'badge-dot-count';
                        navBtn.appendChild(cartBadge);
                    }
                }
                if (cartBadge) {
                    cartBadge.textContent = count > 99 ? '99+' : count;
                    if (count > 0) {
                        cartBadge.style.display = 'flex';
                        cartBadge.animate([
                            { transform: 'scale(1)' },
                            { transform: 'scale(1.45)' },
                            { transform: 'scale(1)' }
                        ], { duration: 300, easing: 'ease-out' });
                    } else {
                        cartBadge.style.display = 'none';
                    }
                }
            } else {
                showToast(data.message, true);
            }
        })
        .catch(() => {
            showToast("Failed to add product to cart.", true);
        });
    });
}

// AJAX Wishlist Toggle
function initAjaxWishlist() {
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('.ajax-wishlist-toggle');
        if (!btn) return;

        e.preventDefault();
        const productId = btn.dataset.productId;
        const csrfToken = getCookie('csrftoken');

        fetch(`/wishlist/toggle/${productId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(res => {
            if (res.status === 403 || res.redirected) {
                window.location.href = '/accounts/login/';
                return;
            }
            return res.json();
        })
        .then(data => {
            if (data && data.require_login) {
                showToast(data.message || "Please log in to manage your wishlist.", true);
                setTimeout(() => {
                    window.location.href = data.redirect_url || '/accounts/login/';
                }, 800);
                return;
            }
            if (data && data.success) {
                showToast(data.message);
                
                // Synchronize all wishlist buttons on current page for this product (e.g. grid & list views)
                const allProductBtns = document.querySelectorAll(`.ajax-wishlist-toggle[data-product-id="${productId}"]`);
                allProductBtns.forEach(b => {
                    const icon = b.querySelector('i');
                    if (data.added) {
                        b.classList.add('active');
                        if (icon) icon.className = 'bi bi-heart-fill';
                    } else {
                        b.classList.remove('active');
                        if (icon) icon.className = 'bi bi-heart';
                    }
                });

                // Update Wishlist Badge Count in navbar
                const count = parseInt(data.wishlist_count, 10) || 0;
                let wishlistBadge = document.getElementById('wishlistBadgeCount');
                
                if (!wishlistBadge) {
                    const navBtn = document.getElementById('wishlistNavBtn') || 
                                   document.querySelector('a[title="Wishlist"]') || 
                                   document.querySelector('a[href*="/wishlist/"]');
                    if (navBtn) {
                        wishlistBadge = document.createElement('span');
                        wishlistBadge.id = 'wishlistBadgeCount';
                        wishlistBadge.className = 'badge-dot-count';
                        navBtn.appendChild(wishlistBadge);
                    }
                }

                if (wishlistBadge) {
                    wishlistBadge.textContent = count > 99 ? '99+' : count;
                    if (count > 0) {
                        wishlistBadge.style.display = 'flex';
                        wishlistBadge.animate([
                            { transform: 'scale(1)' },
                            { transform: 'scale(1.45)' },
                            { transform: 'scale(1)' }
                        ], { duration: 300, easing: 'ease-out' });
                    } else {
                        wishlistBadge.style.display = 'none';
                    }
                }
            } else if (data && data.message) {
                showToast(data.message, true);
            }
        })
        .catch(() => {
            showToast("Failed to update wishlist.", true);
        });
    });
}

// Detail Page Tabs
function initDetailTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');
    if (!tabBtns.length) return;

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.dataset.tab;
            tabBtns.forEach(b => b.classList.remove('active'));
            tabPanes.forEach(p => p.style.display = 'none');

            btn.classList.add('active');
            const targetPane = document.getElementById(target);
            if (targetPane) targetPane.style.display = 'block';
        });
    });
}

// CSRF cookie reader
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
