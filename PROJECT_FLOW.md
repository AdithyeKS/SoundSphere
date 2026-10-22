# SoundSphere - System & User Workflows Documentation

Project Title: **SoundSphere – Modern Headphone E-Commerce Platform**  
Technology Stack: **Python (Django), HTML5, CSS3, JavaScript, MySQL / SQLite**

---

## 🔄 1. Overall System Architecture & Workflows

```
                           ┌─────────────────────────────────┐
                           │      SoundSphere Web App        │
                           │   Django + HTML/CSS/JS + MySQL  │
                           └────────────────┬────────────────┘
                                            │
           ┌────────────────────────────────┼────────────────────────────────┐
           ▼                                ▼                                ▼
┌──────────────────────┐        ┌──────────────────────┐        ┌──────────────────────┐
│  CUSTOMER WORKFLOW   │        │   SELLER WORKFLOW    │        │    ADMIN WORKFLOW    │
└──────────────────────┘        └──────────────────────┘        └──────────────────────┘
```

---

## 👤 2. Customer / User Workflow Diagram

```
                            ┌────────────────────────┐
                            │    Home / Landing      │
                            │ (Hero, Featured, Specs)│
                            └───────────┬────────────┘
                                        │
             ┌──────────────────────────┴──────────────────────────┐
             ▼                                                     ▼
┌────────────────────────┐                             ┌────────────────────────┐
│  Register / Sign In    │                             │ Search & Browse Catalog│
└────────────┬───────────┘                             │(Filter: Brand/Price/ANC)│
             │                                         └───────────┬────────────┘
             └──────────────────────────┬──────────────────────────┘
                                        ▼
                            ┌────────────────────────┐
                            │  Product Detail Page   │
                            │(Specs, Reviews, Stock) │
                            └───────────┬────────────┘
                                        │
      ┌─────────────────────────────────┼─────────────────────────────────┐
      ▼                                 ▼                                 ▼
┌───────────┐                     ┌───────────┐                     ┌───────────┐
│ Wishlist  │                     │Add to Cart│                     │  BUY NOW  │
└─────┬─────┘                     └─────┬─────┘                     └─────┬─────┘
      │ Save                            │ Calculate Subtotal/Tax          │ Instant
      ▼                                 ▼                                 │ Checkout
┌───────────┐                     ┌───────────┐                           │
│ Move to   │                     │ Shopping  │                           │
│   Cart    │────────────────────►│   Cart    │                           │
└───────────┘                     └─────┬─────┘                           │
                                        │ Proceed to Checkout             │
                                        ▼                                 │
                            ┌────────────────────────┐                    │
                            │    Checkout Step 1     │◄───────────────────┘
                            │ (Select/Add Address)   │
                            └───────────┬────────────┘
                                        │
                                        ▼
                            ┌────────────────────────┐
                            │    Checkout Step 2     │
                            │(COD, Card, UPI, Gateway│
                            └───────────┬────────────┘
                                        │ Payment Authorized
                                        ▼
                            ┌────────────────────────┐
                            │   Order Confirmation   │
                            │ (Invoice & Txn Receipt)│
                            └───────────┬────────────┘
                                        │
                                        ▼
                            ┌────────────────────────┐
                            │  My Orders & Tracking  │
                            │(Status & Leave Review) │
                            └────────────────────────┘
```

---

## 🏪 3. Seller Workflow Diagram

```
                            ┌────────────────────────┐
                            │   Seller Registration  │
                            │ (Store, Phone, GSTIN)  │
                            └───────────┬────────────┘
                                        │
                                        ▼
                            ┌────────────────────────┐
                            │     Seller Login       │
                            └───────────┬────────────┘
                                        │
                                        ▼
                            ┌────────────────────────┐
                            │    Seller Dashboard    │
                            │(Revenue, Sold, Stock)  │
                            └───────────┬────────────┘
                                        │
             ┌──────────────────────────┼──────────────────────────┐
             ▼                          ▼                          ▼
┌────────────────────────┐ ┌────────────────────────┐ ┌────────────────────────┐
│  List New Product      │ │  Edit Product & Stock  │ │   Track Store Sales    │
│ (Title, Specs, Price)  │ │ (Update Inventory qty) │ │  (Revenue per item)    │
└────────────────────────┘ └────────────────────────┘ └────────────────────────┘
```

---

## ⚙️ 4. Admin Workflow Diagram

```
                            ┌────────────────────────┐
                            │      Admin Login       │
                            └───────────┬────────────┘
                                        │
                                        ▼
                            ┌────────────────────────┐
                            │ Admin Control Panel    │
                            │(System Revenue, Users) │
                            └───────────┬────────────┘
                                        │
             ┌──────────────────────────┼──────────────────────────┐
             ▼                          ▼                          ▼
┌────────────────────────┐ ┌────────────────────────┐ ┌────────────────────────┐
│ Product & Category CRUD│ │ Order Status Updater   │ │ Django Core Admin      │
│ (Featured Hero Flags)  │ │ (Pending ➔ Delivered)  │ │   (/admin/ Access)     │
└────────────────────────┘ └────────────────────────┘ └────────────────────────┘
```

---

## 📊 5. Backend & Data Process Flow

```
[ User Browser ]
       │
       │ HTTP GET / POST Request (AJAX / Form)
       ▼
[ Django URL Router ] (urls.py)
       │
       │ Matches Route (e.g. /cart/add/, /orders/checkout/)
       ▼
[ View Logic Handler ] (views.py)
       │
       ├──► Checks Authentication & Role Decorators (@login_required, @seller_required)
       ├──► Queries / Mutates Database Models via Django ORM (models.py)
       │
       ▼
[ MySQL / SQLite Database ]
       │
       ├──► Stores User Profile, Shipping Address, Seller Profile
       ├──► Stores Product Catalog, Specs Matrix, Reviews
       ├──► Stores Cart Items, Wishlist Items
       └──► Stores Order, Order Items, Payment Transaction
       │
       ▼
[ HTML Template Renderer ] (templates + static CSS/JS)
       │
       ▼
[ Client Browser Render ] (Glassmorphic Audio UI + Toasts)
```
