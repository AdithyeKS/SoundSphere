# SoundSphere - Step-by-Step Master Prompts Guide

This document contains step-by-step development prompts for **SoundSphere**. Each prompt is designed to build the frontend HTML pages first, followed by dynamic Django backend integration (MySQL database, Admin page, User page, Seller page, Payment simulation, and real DB CRUD without hardcoded sample data).

---

## 📌 Phase 1: Project Setup & Database Configuration Prompt

```text
Create a Django e-commerce project named 'soundsphere'.
Configure 'soundsphere/settings.py' to connect to a MySQL database named 'soundsphere_db' using PyMySQL, with an automatic fallback to SQLite for local development. 
Create Django apps for:
1. accounts (User authentication, roles, address book, feedback)
2. products (Headphones, accessories, categories, brands, specs, reviews)
3. cart (Cart & session cart management)
4. wishlist (Saved items)
5. orders (Checkout, payments, order tracking)
6. admin_panel (Custom Admin dashboard)
7. sellers (Seller portal & seller dashboard)

Configure static files, media upload directories, templates folder, and URL routing.
```

---

## 🎨 Phase 2: Design System & Base Layout Prompt (HTML/CSS/JS First)

```text
Design a modern dark-mode frontend layout for SoundSphere using HTML5, CSS3, and JavaScript.
Theme: Cyber Cyan (#00f2fe), Electric Indigo (#4facfe), Dark Midnight background (#07090e), glassmorphic cards, and neon audio-wave glow.

Create 'templates/base.html' containing:
1. Glassmorphic Sticky Header with Brand logo, Navigation links (Home, Headphones, Accessories, All Products, Feedback).
2. Live Search input bar with AJAX dropdown.
3. Wishlist badge counter and Cart badge counter.
4. User Role Navigation menu:
   - For Customers: 'Sign In', 'My Account', 'My Orders'.
   - For Sellers: 'Seller Portal', 'My Store Dashboard'.
   - For Admins: 'Admin Dashboard', 'Django Admin'.
5. Dynamic Toast notification container.
6. Footer with categorized site links and copyright notice.

CRITICAL REQUIREMENT: Do not hardcode static sample products inside HTML templates. All product cards, titles, prices, ratings, and specs must render dynamically using Django template tags from the database context.
```

---

## 👥 Phase 3: User Roles & Authentication Models Prompt (Database Layer)

```text
Build Django authentication models with role-based authorization in 'accounts/models.py' and 'sellers/models.py':

1. UserProfile Model:
   - user (OneToOne with User)
   - role (choices: 'customer', 'seller', 'admin')
   - phone, avatar, bio, created_at
   - is_seller property getter

2. SellerProfile Model:
   - user (OneToOne with User)
   - store_name (unique)
   - phone, tax_id (GSTIN/Business Tax ID), store_description
   - is_approved (boolean)

3. ShippingAddress Model:
   - user (ForeignKey to User)
   - full_name, phone_number, street_address, apartment_address, city, state, postal_code, country, is_default

4. CustomerFeedback Model:
   - user (optional ForeignKey), name, email, category, subject, message, rating, created_at

Create registration and login templates for Customers ('templates/accounts/register.html', 'login.html') and Sellers ('templates/sellers/register.html', 'login.html'). Include password hashing, CSRF protection, and logout views.
```

---

## 🎧 Phase 4: Product Catalog, Specs & Dynamic Database Schema Prompt

```text
Design the product database models in 'products/models.py':

1. Category Model: name, slug, description, image, is_accessory (boolean for Headphones vs Accessories).
2. Brand Model: name, slug, logo, description.
3. Product Model:
   - seller (ForeignKey to User, null=True)
   - brand (ForeignKey to Brand)
   - category (ForeignKey to Category)
   - name, slug, price, discount_price, description, stock
   - is_featured, is_active, image, created_at
   - Properties for current_price, is_on_sale, discount_percentage, average_rating, review_count.
4. ProductSpec Model: driver_size, battery_life, connectivity, noise_cancellation, frequency_response, impedance, weight, warranty.
5. Review Model: product, user, rating (1-5), headline, comment, created_at.

Create views and HTML templates:
- 'templates/home.html': Hero banner with audio wave animation, category grid, featured products from DB, top brands.
- 'templates/products/list.html': Catalog with dynamic category filter, brand filter, price range, sorting, and AJAX search.
- 'templates/products/detail.html': Full image, tech specs matrix table, stock status indicator, user reviews list, review submission form, 'Add to Cart', and instant 'Buy Now' button.
```

---

## 🛒 Phase 5: Cart, Wishlist & "Buy Now" Backend Prompt

```text
Develop cart and wishlist backend logic:

1. Cart Module ('cart/'):
   - Cart & CartItem models supporting guest session cart merging upon user login.
   - Views for AJAX Add to Cart, Quantity Update, and Item Removal.
   - Promo Coupon handler ('SOUND10' for 10% discount).
   - Instant 'Buy Now' view: Adds item to cart and immediately redirects to Checkout.
   - Context processor providing live 'cart_item_count' to all templates.

2. Wishlist Module ('wishlist/'):
   - Wishlist & WishlistItem models.
   - AJAX 1-click Heart Toggle view.
   - 'Move to Cart' view transfer.
   - Context processor providing 'wishlist_count' to templates.

HTML Templates: 'templates/cart/cart.html' and 'templates/wishlist/wishlist.html'.
```

---

## 💳 Phase 6: Checkout, Payment Simulation & Order Management Prompt

```text
Create the checkout and order management pipeline in 'orders/':

1. Models:
   - Order: order_number (unique hex ID), user, full_name, email, phone, street_address, city, state, postal_code, country, subtotal, tax, shipping, discount, total_amount, status (Pending, Processing, Shipped, Delivered, Cancelled), payment_status (Unpaid, Paid).
   - OrderItem: order, product, product_name, price, quantity.
   - Payment: order, payment_method (card, upi, netbanking, cod), transaction_id, amount, status.

2. Views & HTML Templates:
   - 'templates/orders/checkout.html': Saved shipping address selector + new address input form.
   - 'templates/orders/payment.html': Payment gateway modal supporting Cash on Delivery (COD), Credit/Debit Card, UPI / Instant QR Code, Net Banking, and Online Gateway (Razorpay / Stripe placeholder keys).
   - Process Payment View: Wraps order creation, order items snapshot, payment record creation, inventory stock deduction, and cart cleanup inside Django 'transaction.atomic()'.
   - 'templates/orders/confirmation.html': Invoice receipt page with printable summary.
   - 'templates/orders/my_orders.html' & 'order_detail.html': Customer order status tracking timeline.
```

---

## 🏪 Phase 7: Seller Portal & Dashboard Prompt

```text
Build a dedicated Seller Portal in 'sellers/':

1. Role Authorization: Create a '@seller_required' view decorator restricting portal access to accounts with 'is_seller=True'.
2. Seller Dashboard ('templates/sellers/dashboard.html'):
   - Analytics cards: Listed Products Count, Gross Sales Revenue from seller items, Units Sold, Low Stock Warnings (stock <= 5).
   - Recent Store Sales table.
3. Seller Catalog Management ('templates/sellers/products_list.html' & 'product_form.html'):
   - Form for sellers to list new headphones/accessories with photos and tech specs.
   - Edit product price, discount, and stock count.
   - Delete listed products.
4. Seller Sales Orders View ('templates/sellers/orders_list.html'): View orders containing items sold by the seller.
```

---

## ⚙️ Phase 8: Admin Control Panel & Feedback Module Prompt

```text
Build administrative oversight in 'admin_panel/' and 'accounts/':

1. Admin Dashboard ('templates/admin_panel/dashboard.html'):
   - System overview metrics: Total Products, Customer Orders Count, Total System Revenue, Low Stock Alerts.
   - Recent Customer Orders table.
2. Product & Order Management:
   - Admin Product List ('templates/admin_panel/products_list.html') & Form ('product_form.html').
   - Order Status Updater ('templates/admin_panel/orders_list.html'): Dropdown form to update order status ('Pending' -> 'Processing' -> 'Shipped' -> 'Delivered' -> 'Cancelled').
3. Customer Feedback Module ('accounts/views.py' & 'templates/accounts/feedback.html'):
   - Form for visitors/customers to send feedback/inquiries (Category, Subject, Message, Rating).
   - Registered under Django Admin for inspection.
```

---

## 🧪 Phase 9: Database Migrations, Seeding & Testing Prompt

```text
1. Execute database migrations:
   python manage.py makemigrations accounts products cart wishlist orders sellers
   python manage.py migrate

2. Create a custom Django management command ('products/management/commands/seed_data.py') to populate initial categories, brands, tech specs, and admin credentials ('admin' / 'admin123').

3. Run automated tests:
   python manage.py test

4. Launch development server:
   python manage.py runserver 0.0.0.0:8000
```
