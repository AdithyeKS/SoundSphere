# SoundSphere - Project Modules Documentation

Project Title: **SoundSphere – Modern Headphone & Audio Accessories E-Commerce Platform**  
Technology Stack: **Python (Django), HTML5, CSS3, JavaScript, MySQL / SQLite**

---

## 📋 Table of Contents
1. [Overview of All Modules](#overview-of-all-modules)
2. [Modules Categorized by User Roles](#modules-categorized-by-user-roles)
3. [Database Entity Mappings](#database-entity-mappings)

---

## 📦 Overview of All Modules

### 1. User Authentication & Account Management Module (`accounts`)
- **Purpose:** Manages secure customer registration, login, profile editing, and shipping address book.
- **Key Features:**
  - Customer & Seller registration and authentication.
  - Role-based permissions (`customer`, `seller`, `admin`).
  - Saved Address Book (Add, edit, delete, set default shipping address).
  - Password hashing and CSRF security.

### 2. Seller Portal & Storefront Module (`sellers`)
- **Purpose:** Enables independent sellers/vendors to register, list headphones, and manage inventory and sales.
- **Key Features:**
  - Store Profile Registration (Store Name, Phone, GSTIN / Tax ID, Description).
  - Seller Analytics Dashboard (Total Revenue, Units Sold, Listed Products).
  - Seller Product CRUD (Add headphones/accessories, edit specs, update stock).
  - Seller Sales Tracking for items sold by the store.

### 3. Product Catalog & Technical Specifications Module (`products`)
- **Purpose:** Manages headphone categories, brands, tech specs, catalog filtering, and searching.
- **Key Features:**
  - **Headphone Categories:** Wireless Headphones, Gaming Headsets, Bluetooth Earbuds, Studio Monitors, Active Noise-Cancelling (ANC).
  - **Accessories Categories:** Headphone Stands, Carrying Cases, Ear Cushions, Audio Cables.
  - Brand filtering (Sony, Bose, Sennheiser, Audio-Technica, JBL, SoundSphere Signature).
  - Price range, category, brand, and sorting filters (Price low/high, newest).
  - Live AJAX Search input with dropdown suggestions.
  - Technical Specs Matrix: Driver size, battery life, connectivity, noise cancellation, frequency response, impedance, weight, warranty.

### 4. Wishlist Module (`wishlist`)
- **Purpose:** Saves favorite headphones for future reference.
- **Key Features:**
  - AJAX 1-click heart toggle (Save/Remove).
  - Dynamic wishlist count badge.
  - Direct "Move to Cart" button.

### 5. Shopping Cart & Promo Coupon Module (`cart`)
- **Purpose:** Real-time cart management supporting guest session carts and user carts.
- **Key Features:**
  - Dynamic quantity increment, decrement, and item removal via AJAX.
  - Stock availability check.
  - Promo Coupons (`SOUND10` for 10% off, `VIP20` for 20% off).
  - Auto-calculation: Subtotal + 8% Tax + Shipping charge.

### 6. Checkout & Instant "Buy Now" Module (`orders`)
- **Purpose:** Handles shipping selection, order preview, and payment authorization.
- **Key Features:**
  - **Buy Now** instant checkout bypassing the cart page.
  - Address selection from saved address book or new entry.
  - Multi-method Payment Simulation: Cash on Delivery (COD), Credit/Debit Card, UPI / QR Code, Net Banking.
  - Online Gateway Ready (Razorpay / Stripe placeholder configuration).
  - Stock auto-deduction upon payment.

### 7. Order History & Invoice Receipt Module (`orders`)
- **Purpose:** Order tracking and printable invoice receipt generation.
- **Key Features:**
  - Order status timeline (`Pending` ➔ `Processing` ➔ `Shipped` ➔ `Delivered`).
  - Printable invoice receipt with unique Transaction ID (`TXN-...`).

### 8. Customer Reviews & Ratings Module (`products`)
- **Purpose:** Customer feedback and rating system for headphones.
- **Key Features:**
  - 1–5 Star rating system.
  - Review headline and written review submission.
  - Dynamic average rating calculation.

### 9. Customer Feedback & Inquiry Module (`accounts`)
- **Purpose:** Allows customers and website visitors to submit general inquiries, product questions, order support requests, and site suggestions.
- **Key Features:**
  - Interactive Feedback submission form (`/accounts/feedback/`).
  - Category categorization (General, Product & Specs, Order & Delivery, Site Feedback).
  - 1–5 Star overall website experience rating.
  - Admin inspection panel for customer inquiries.

### 10. Admin Management Dashboard (`admin_panel`)
- **Purpose:** Centralized administrative control interface.
- **Key Features:**
  - Analytics (Total Products, Total Orders, Total Revenue).
  - Low-stock warning alert table (Stock ≤ 5 units).
  - System-wide product CRUD & Order status updater.

---

## 👥 Modules Categorized by User Roles

### 👤 1. Customer Roles & Modules
- Account Registration & Login
- Shipping Address Book
- Product Search & Filtering
- Technical Specs & Reviews Viewing
- Wishlist & Save Items
- Shopping Cart & Coupon Discount
- Buy Now & Multi-Step Checkout
- Payment Simulation (COD, Card, UPI, Gateway)
- Order Tracking & Invoice Receipt Printing
- Product Rating & Review Submission
- Customer Feedback & General Inquiries Submission

### 🏪 2. Seller Roles & Modules
- Seller Portal Registration & Login (`/seller/register/`, `/seller/login/`)
- Seller Sales Analytics Dashboard (`/seller/dashboard/`)
- Product & Accessories Listing Form (Photos, Price, Discount, Specs)
- Stock Count Management & Low-Stock Alerts
- Seller Sales Orders Tracking

### ⚙️ 3. Admin Roles & Modules
- Admin Dashboard Overview (`/admin-panel/` & `/admin/`)
- Full System CRUD on Categories, Brands, Products
- Home Page Hero Featured Flags Toggle
- Order Status Fulfillment Updater (`Pending` ➔ `Processing` ➔ `Shipped` ➔ `Delivered` ➔ `Cancelled`)
- Inspect Submitted Customer Feedbacks & Inquiries
- System Revenue & User Oversight

---

## 🗄️ Database Entity Mappings

| Module | Core Models | Key Fields |
| :--- | :--- | :--- |
| **Accounts** | `User`, `UserProfile`, `ShippingAddress`, `CustomerFeedback` | `username`, `email`, `role`, `phone`, `street_address`, `city`, `subject`, `message`, `rating` |
| **Sellers** | `SellerProfile` | `user`, `store_name`, `phone`, `tax_id`, `store_description`, `is_approved` |
| **Products** | `Category`, `Brand`, `Product`, `ProductSpec`, `Review` | `name`, `seller`, `category`, `price`, `discount_price`, `stock`, `driver_size`, `battery_life`, `rating` |
| **Wishlist** | `Wishlist`, `WishlistItem` | `user`, `product`, `added_at` |
| **Cart** | `Cart`, `CartItem` | `user`, `session_id`, `product`, `quantity` |
| **Orders** | `Order`, `OrderItem`, `Payment` | `order_number`, `user`, `total_amount`, `status`, `payment_status`, `payment_method`, `transaction_id` |
