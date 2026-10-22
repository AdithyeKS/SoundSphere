# SoundSphere Database Schema Documentation

## 🗄️ DATABASE DESIGN SCHEMA (Normalized Notation)

```text
DATABASE DESIGN SCHEMA (SoundSphere Production & Implementation Architecture)

auth_user(id PK, username UNIQUE, email, password, first_name, last_name, is_staff, is_active, date_joined)
user_profiles(id PK, user_id FK→auth_user.id UNIQUE, role, phone, bio, created_at, updated_at)
seller_profiles(id PK, user_id FK→auth_user.id UNIQUE, store_name UNIQUE, tagline, store_description, phone, tax_id, location, state, logo, status, rejection_reason, created_at)
shipping_addresses(id PK, user_id FK→auth_user.id, full_name, phone_number, street_address, apartment_address, city, state, postal_code, country, is_default, created_at)
categories(id PK, name UNIQUE, slug UNIQUE, description, image, is_accessory, created_at)
products(id PK, seller_id FK→seller_profiles.id, category_id FK→categories.id, name, slug UNIQUE, price, discount_price, description, stock, is_featured, is_active, approval_status, rejection_reason, image, driver_size, battery_life, connectivity, noise_cancellation, frequency_response, impedance, weight, warranty, created_at, updated_at)
reviews(id PK, product_id FK→products.id, user_id FK→auth_user.id, rating, headline, comment, created_at)
carts(id PK, user_id FK→auth_user.id UNIQUE, session_id, created_at, updated_at)
cart_items(id PK, cart_id FK→carts.id, product_id FK→products.id, quantity, added_at)
orders(order_number PK, user_id FK→auth_user.id, full_name, email, phone, street_address, apartment_address, city, state, postal_code, country, subtotal, tax, shipping, discount, total_amount, status, payment_status, created_at, updated_at)
order_items(id PK, order_id FK→orders.order_number, product_id FK→products.id, product_name, price, quantity)
payments(id PK, order_id FK→orders.order_number UNIQUE, payment_method, transaction_id UNIQUE, amount, status, created_at)
wishlists(id PK, user_id FK→auth_user.id UNIQUE, created_at)
wishlist_items(id PK, wishlist_id FK→wishlists.id, product_id FK→products.id, added_at)
customer_feedbacks(id PK, user_id FK→auth_user.id, name, email, category, subject, message, rating, created_at)
notifications(id PK, user_id FK→auth_user.id, title, message, notification_type, link, is_read, created_at)
```

---

## 📋 Full Data Dictionary Tables

### 1. Table Name: `auth_user`
**Description**: Core Django user authentication table.

| Field Name | Data Type | Key | Description / Constraints |
|---|---|---|---|
| `id` | `BigInteger` | `PK` | Auto Increment, Primary Key |
| `username` | `Varchar(150)` | `Unique` | Required. Unique username for authentication |
| `email` | `Varchar(254)` | - | User email address |
| `password` | `Varchar(128)` | - | PBKDF2 hashed password string |
| `first_name` | `Varchar(150)` | - | User first name |
| `last_name` | `Varchar(150)` | - | User last name |
| `is_staff` | `Boolean` | - | Staff / Admin control panel access flag |
| `is_active` | `Boolean` | - | Account active status flag |
| `date_joined` | `DateTime` | - | Account creation timestamp |

---

### 2. Table Name: `user_profiles`
**Description**: Extends `auth_user` with application roles and user metadata. One-to-One extension table — `user_id` is both the **Primary Key** and **Foreign Key**, eliminating the need for a separate surrogate `id`.

| Field Name | Data Type | Key | Description / Constraints |
|---|---|---|---|
| `user_id` | `BigInteger` | `PK, FK` | **Primary Key & Foreign Key** to `auth_user.id` (One-to-One, CASCADE). Uniquely identifies the profile. |
| `role` | `Varchar(20)` | - | Choices: `customer`, `seller`, `admin`, Default: `'customer'` |
| `phone` | `Varchar(20)` | - | Nullable. Contact phone number |
| `bio` | `Text` | - | Nullable. Short user bio/profile description |
| `created_at` | `DateTime` | - | Timestamp created |
| `updated_at` | `DateTime` | - | Timestamp updated |

---

### 3. Table Name: `seller_profiles`
**Description**: Seller brand registrations, store metadata, tax ID, and approval status. One-to-One extension — `user_id` is the **Primary Key & Foreign Key**. `store_name` acts as a natural **Alternate / Candidate Key**. `status` (`pending`, `approved`, `rejected`) serves as the single source of truth for seller moderation.

| Field Name | Data Type | Key | Description / Constraints |
|---|---|---|---|
| `user_id` | `BigInteger` | `PK, FK` | **Primary Key & Foreign Key** to `auth_user.id` (One-to-One, CASCADE). Uniquely identifies the seller account. |
| `store_name` | `Varchar(150)` | `Unique` | Required. Registered brand / store name. *(Alternate / Candidate Key)* |
| `tagline` | `Varchar(200)` | - | Nullable. Brand slogan / tagline |
| `store_description` | `Text` | - | Nullable. Full store description |
| `phone` | `Varchar(20)` | - | Required. Business contact phone |
| `tax_id` | `Varchar(50)` | - | Nullable. Business GSTIN / Tax ID |
| `location` | `Varchar(150)` | - | Nullable. Store location / pickup city |
| `logo` | `Varchar(100)` | - | Nullable. Brand logo image path |
| `status` | `Varchar(20)` | - | Choices: `pending`, `approved`, `rejected`, Default: `'pending'`. Single source of truth for moderation. |
| `rejection_reason` | `Text` | - | Nullable. Admin feedback if application rejected |
| `created_at` | `DateTime` | - | Timestamp registration submitted |

---

### 4. Table Name: `shipping_addresses`
**Description**: Saved customer delivery addresses.

| Field Name | Data Type | Key | Description / Constraints |
|---|---|---|---|
| `id` | `BigInteger` | `PK` | Auto Increment, Primary Key |
| `user_id` | `BigInteger` | `FK` | Foreign Key to `auth_user.id` (CASCADE) |
| `full_name` | `Varchar(100)` | - | Required. Recipient full name |
| `phone_number` | `Varchar(20)` | - | Required. Delivery phone number |
| `street_address` | `Varchar(255)` | - | Required. House number & street |
| `apartment_address` | `Varchar(255)` | - | Nullable. Apartment / Suite number |
| `city` | `Varchar(100)` | - | Required. City |
| `state` | `Varchar(100)` | - | Required. State / Province |
| `postal_code` | `Varchar(20)` | - | Required. ZIP / Postal code |
| `country` | `Varchar(100)` | - | Default: `'United States'` |
| `is_default` | `Boolean` | - | Default primary address flag, Default: `False` |
| `created_at` | `DateTime` | - | Timestamp address created |

---

### 5. Table Name: `categories`
**Description**: Product classification categories. Uses standard auto-increment `id` PK for fast database joins, with `name` and `slug` as natural **Alternate / Candidate Keys** for routing and search.

| Field Name | Data Type | Key | Description / Constraints |
|---|---|---|---|
| `id` | `BigInteger` | `PK` | Auto Increment, Primary Key |
| `name` | `Varchar(100)` | `Unique` | Required. Category display title. *(Alternate Key)* |
| `slug` | `Varchar(120)` | `Unique` | Auto-generated URL slug. *(Alternate Key)* |
| `description` | `Text` | - | Nullable. Category overview |
| `image` | `Varchar(100)` | - | Nullable. Category image file path |
| `is_accessory` | `Boolean` | - | Accessory flag, Default: `False` |
| `created_at` | `DateTime` | - | Timestamp category created |

---

### 6. Table Name: `products`
**Description**: Headset product catalog, acoustic specifications, pricing, stock, and moderation status. `id` serves as surrogate PK for foreign key joins, while `slug` is a natural **Alternate Key** for human-readable SEO URLs.

| Field Name | Data Type | Key | Description / Constraints |
|---|---|---|---|
| `id` | `BigInteger` | `PK` | Auto Increment, Primary Key |
| `name` | `Varchar(200)` | - | Required. Headset product title |
| `slug` | `Varchar(220)` | `Unique` | Unique SEO URL slug. *(Alternate Key)* |
| `seller_id` | `BigInteger` | `FK` | Foreign Key to `seller_profiles.id` (SET_NULL, Nullable) |
| `category_id` | `BigInteger` | `FK` | Foreign Key to `categories.id` (CASCADE) |
| `price` | `Decimal(10,2)` | - | Required. Original price (INR) |
| `discount_price` | `Decimal(10,2)` | - | Nullable. Sale price (INR) |
| `description` | `Text` | - | Required. Detailed product overview |
| `stock` | `Integer` | - | Available units, Default: `10` |
| `is_featured` | `Boolean` | - | Featured on homepage flag, Default: `False` |
| `is_active` | `Boolean` | - | Live in catalog status flag, Default: `True` |
| `approval_status` | `Varchar(20)` | - | Choices: `pending`, `approved`, `rejected`, Default: `'approved'` |
| `rejection_reason` | `Text` | - | Nullable. Rejection feedback |
| `image` | `Varchar(100)` | - | Nullable. Headset primary image file path |
| `driver_size` | `Varchar(50)` | - | Spec: e.g. 40mm Dynamic (Nullable) |
| `battery_life` | `Varchar(50)` | - | Spec: e.g. 30 Hours (Nullable) |
| `connectivity` | `Varchar(100)` | - | Spec: e.g. Bluetooth 5.3 (Nullable) |
| `noise_cancellation` | `Varchar(100)` | - | Spec: e.g. ANC Hybrid (Nullable) |
| `frequency_response` | `Varchar(50)` | - | Spec: e.g. 20Hz - 20,000Hz (Nullable) |
| `impedance` | `Varchar(50)` | - | Spec: e.g. 32 Ohms (Nullable) |
| `weight` | `Varchar(50)` | - | Spec: e.g. 250g (Nullable) |
| `warranty` | `Varchar(50)` | - | Spec: e.g. 1 Year Warranty (Nullable) |
| `created_at` | `DateTime` | - | Timestamp product created |
| `updated_at` | `DateTime` | - | Timestamp product updated |

---

### 7. Table Name: `reviews`
**Description**: Product reviews & customer star ratings. Uses standard surrogate `id` PK with a foreign key to `products` and `auth_user`.

| Field Name | Data Type | Key | Description / Constraints |
|---|---|---|---|
| `id` | `BigInteger` | `PK` | Auto Increment, Primary Key |
| `product_id` | `BigInteger` | `FK` | Foreign Key to `products.id` (CASCADE) |
| `user_id` | `BigInteger` | `FK` | Foreign Key to `auth_user.id` (CASCADE) |
| `rating` | `SmallInteger` | - | Star rating (1 to 5), Default: `5` |
| `headline` | `Varchar(150)` | - | Required. Review title |
| `comment` | `Text` | - | Required. Customer feedback comment |
| `created_at` | `DateTime` | - | Timestamp review posted |

---

### 8. Table Name: `orders`
**Description**: Customer purchase orders, pricing summary, and fulfillment tracking. `order_number` is promoted to **Natural Primary Key**, eliminating the redundant surrogate `id`.

| Field Name | Data Type | Key | Description / Constraints |
|---|---|---|---|
| `order_number` | `Varchar(50)` | `PK` | **Natural Primary Key.** Unique business-formatted code (e.g. `SS-A1B2C3D4`). Promoted from Alternate Key to PK. |
| `user_id` | `BigInteger` | `FK` | Foreign Key to `auth_user.id` (SET_NULL, Nullable) |
| `full_name` | `Varchar(100)` | - | Required. Recipient name |
| `email` | `Varchar(254)` | - | Required. Email address |
| `phone` | `Varchar(20)` | - | Required. Contact phone number |
| `street_address` | `Varchar(255)` | - | Required. Street address |
| `apartment_address` | `Varchar(255)` | - | Nullable. Apartment / Suite |
| `city` | `Varchar(100)` | - | Required. City |
| `state` | `Varchar(100)` | - | Required. State / Province |
| `postal_code` | `Varchar(20)` | - | Required. ZIP / Postal code |
| `country` | `Varchar(100)` | - | Default: `'United States'` |
| `subtotal` | `Decimal(10,2)` | - | Required. Items subtotal |
| `tax` | `Decimal(10,2)` | - | Required. Tax amount |
| `shipping` | `Decimal(10,2)` | - | Required. Shipping charge |
| `discount` | `Decimal(10,2)` | - | Default: `0.00` |
| `total_amount` | `Decimal(10,2)` | - | Required. Grand total paid |
| `status` | `Varchar(20)` | - | Choices: `Pending`, `Confirmed`, `Packed`, `Shipped`, `Out for Delivery`, `Delivered`, `Cancelled`, `Returned`, Default: `'Pending'` |
| `payment_status` | `Varchar(20)` | - | Choices: `Unpaid`, `Paid`, `Refunded`, Default: `'Unpaid'` |
| `created_at` | `DateTime` | - | Timestamp order placed |
| `updated_at` | `DateTime` | - | Timestamp status last updated |

---

### 9. Table Name: `order_items`
**Description**: Individual product line items within an order. Junction table between `orders` and `products` — uses a **Composite Primary Key** `(order_number, product_id)` instead of a surrogate `id`. This naturally enforces that the same product cannot be duplicated in the same order.

| Field Name | Data Type | Key | Description / Constraints |
|---|---|---|---|
| `order_number` | `Varchar(50)` | `PK (Composite)` | **Part of Composite PK.** Foreign Key to `orders.order_number` (CASCADE) |
| `product_id` | `BigInteger` | `PK (Composite)` | **Part of Composite PK.** Foreign Key to `products.product_id` (PROTECT) |
| `product_name` | `Varchar(200)` | - | Product title snapshot at time of purchase |
| `price` | `Decimal(10,2)` | - | Unit price snapshot at purchase time |
| `quantity` | `Integer` | - | Quantity purchased, Default: `1` |

> **Composite PK Constraint**: `PRIMARY KEY (order_number, product_id)` — Ensures one entry per product per order.

---

### 10. Table Name: `payments`
**Description**: Payment transaction records. One-to-One relationship with `orders` — `order_number` is promoted to serve as both **Primary Key and Foreign Key**, removing the redundant surrogate `id`. `transaction_id` is a natural **Alternate Key** from the payment gateway.

| Field Name | Data Type | Key | Description / Constraints |
|---|---|---|---|
| `order_number` | `Varchar(50)` | `PK, FK` | **Primary Key & Foreign Key** to `orders.order_number` (One-to-One, CASCADE). Uniquely identifies the payment record. |
| `payment_method` | `Varchar(30)` | - | Choices: `card`, `upi`, `netbanking`, `cod`, Default: `'card'` |
| `transaction_id` | `Varchar(100)` | `Unique` | Unique payment gateway transaction ID. *(Alternate / Candidate Key)* |
| `amount` | `Decimal(10,2)` | - | Amount paid |
| `status` | `Varchar(20)` | - | Transaction status, Default: `'Success'` |
| `created_at` | `DateTime` | - | Timestamp transaction logged |

---

### 11. Table Name: `carts`
**Description**: Active shopping carts per user or guest session. Uses a `cart_id` surrogate PK for stable FK references from `cart_items`. `user_id` is a Unique FK for the One-to-One user relationship (supports guest carts via `session_id` where `user_id` is NULL).

| Field Name | Data Type | Key | Description / Constraints |
|---|---|---|---|
| `cart_id` | `BigInteger` | `PK` | Auto Increment, Primary Key |
| `user_id` | `BigInteger` | `FK, Unique` | Foreign Key to `auth_user.id` (One-to-One, Nullable, CASCADE). NULL for guest sessions. |
| `session_id` | `Varchar(200)` | - | Nullable. Guest browser session key |
| `created_at` | `DateTime` | - | Timestamp cart created |
| `updated_at` | `DateTime` | - | Timestamp cart updated |

---

### 12. Table Name: `cart_items`
**Description**: Products added to a cart. Many-to-Many junction table between `carts` and `products`. Uses a **Composite Primary Key** `(cart_id, product_id)` eliminating the redundant surrogate `id`. Naturally prevents adding the same product twice to the same cart.

| Field Name | Data Type | Key | Description / Constraints |
|---|---|---|---|
| `cart_id` | `BigInteger` | `PK (Composite)` | **Part of Composite PK.** Foreign Key to `carts.cart_id` (CASCADE) |
| `product_id` | `BigInteger` | `PK (Composite)` | **Part of Composite PK.** Foreign Key to `products.product_id` (CASCADE) |
| `quantity` | `Integer` | - | Units added, Default: `1` |
| `added_at` | `DateTime` | - | Timestamp item added |

> **Composite PK Constraint**: `PRIMARY KEY (cart_id, product_id)` — Ensures a product appears only once per cart.

---

### 13. Table Name: `wishlists`
**Description**: User saved wishlists. One-to-One relationship with `auth_user` — `user_id` serves as both **Primary Key and Foreign Key**, removing the redundant surrogate `id`.

| Field Name | Data Type | Key | Description / Constraints |
|---|---|---|---|
| `user_id` | `BigInteger` | `PK, FK` | **Primary Key & Foreign Key** to `auth_user.id` (One-to-One, CASCADE). Each user has exactly one wishlist. |
| `created_at` | `DateTime` | - | Timestamp wishlist created |

---

### 14. Table Name: `wishlist_items`
**Description**: Saved headsets inside a wishlist. Many-to-Many junction table between `wishlists` and `products`. Uses a **Composite Primary Key** `(user_id, product_id)` directly — removing both the surrogate `id` and the now-redundant `wishlist_id` column (since `wishlists.user_id` IS the PK, we reference it directly).

| Field Name | Data Type | Key | Description / Constraints |
|---|---|---|---|
| `user_id` | `BigInteger` | `PK (Composite)` | **Part of Composite PK.** Foreign Key to `wishlists.user_id` (CASCADE) |
| `product_id` | `BigInteger` | `PK (Composite)` | **Part of Composite PK.** Foreign Key to `products.product_id` (CASCADE) |
| `added_at` | `DateTime` | - | Timestamp item added |

> **Composite PK Constraint**: `PRIMARY KEY (user_id, product_id)` — Ensures a product is saved only once in a user's wishlist.

---

### 15. Table Name: `customer_feedbacks`
**Description**: Support tickets & customer feedback inquiries. Uses `feedback_id` surrogate PK — a natural key does not exist for feedback submissions. `user_id` is Nullable (allows anonymous submissions).

| Field Name | Data Type | Key | Description / Constraints |
|---|---|---|---|
| `feedback_id` | `BigInteger` | `PK` | Auto Increment, Primary Key |
| `user_id` | `BigInteger` | `FK` | Foreign Key to `auth_user.id` (SET_NULL, Nullable). Allows guest/anonymous feedback. |
| `name` | `Varchar(100)` | - | Submitter name |
| `email` | `Varchar(254)` | - | Submitter email address |
| `category` | `Varchar(30)` | - | Choices: `general`, `product`, `order`, `website`, Default: `'general'` |
| `subject` | `Varchar(200)` | - | Subject line |
| `message` | `Text` | - | Detailed message content |
| `rating` | `SmallInteger` | - | Star rating, Default: `5` |
| `created_at` | `DateTime` | - | Timestamp feedback submitted |

---

### 16. Table Name: `notifications`
**Description**: System alerts & moderation notifications. Uses `notification_id` surrogate PK — no natural unique identifier exists for notifications.

| Field Name | Data Type | Key | Description / Constraints |
|---|---|---|---|
| `notification_id` | `BigInteger` | `PK` | Auto Increment, Primary Key |
| `user_id` | `BigInteger` | `FK` | Foreign Key to `auth_user.id` (CASCADE) |
| `title` | `Varchar(200)` | - | Alert title |
| `message` | `Text` | - | Notification message text |
| `notification_type` | `Varchar(20)` | - | Choices: `order`, `product`, `stock`, `system`, Default: `'system'` |
| `link` | `Varchar(255)` | - | Nullable. Action link URL |
| `is_read` | `Boolean` | - | Read status flag, Default: `False` |
| `created_at` | `DateTime` | - | Timestamp alert created |

---

## ⚠️ Normalization Verdict & Intentional Denormalization

### Overall Status

The SoundSphere schema satisfies **1NF**, **2NF**, and **3NF** across all 16 tables.

A small number of fields are **intentionally denormalized** — they technically violate strict 3NF (derivability) or introduce a partial-dependency risk, but are retained because they serve critical business, financial, or audit purposes. These are documented below with full justification.

---

### Intentional Denormalization Register

| # | Table | Field(s) | Normal Form Concern | Justification | Verdict |
|---|---|---|---|---|---|
| 1 | `orders` | `subtotal` | Derivable from `SUM(order_items.price × quantity)` — technically a transitive/derived value | **Historical financial snapshot.** The `subtotal` locks in the pre-tax item total at the moment of checkout. If product prices change or items are later deleted, this value must remain unchanged for invoice accuracy and dispute resolution. | ✅ Retained — Deliberate Snapshot |
| 2 | `orders` | `tax`, `shipping`, `discount` | Each is derivable from a business rule applied to `subtotal` | **Financial audit trail.** Tax rates, shipping fees, and promotional discounts can change over time. Storing the exact values applied at checkout ensures reproducible invoices and supports refund/reversal calculations. | ✅ Retained — Deliberate Snapshot |
| 3 | `orders` | `total_amount` | Derivable as `subtotal + tax + shipping − discount` | **Redundant but essential.** `total_amount` is the legally billed amount. Recomputing it at read time risks inconsistency if any component field were ever corrected. Storing it directly guarantees what was charged matches what is displayed. | ✅ Retained — Deliberate Snapshot |
| 4 | `orders` | `full_name`, `email`, `phone`, `street_address`, `city`, `state`, `postal_code`, `country` | Customer details also exist in `auth_user` and `shipping_addresses` | **Shipping address snapshot.** At the time of order placement, the delivery address is copied into the order record. If the customer later updates or deletes their saved address, the original shipping destination for the order is preserved for dispatch and delivery proof. | ✅ Retained — Deliberate Snapshot |
| 5 | `order_items` | `product_name` | Functionally dependent only on `product_id` — a partial dependency on the composite PK `(order_number, product_id)` | **Product catalog snapshot.** A seller may rename, restock, or deactivate a product. `product_name` is captured at checkout so every order line item permanently reflects the exact product title the customer saw and purchased, regardless of future catalog changes. | ✅ Retained — Deliberate Snapshot |
| 6 | `order_items` | `price` | Functionally dependent only on `product_id` — a partial dependency on the composite PK `(order_number, product_id)` | **Price snapshot.** Product pricing changes over time (discounts, repricing). The `price` stored in `order_items` is the per-unit price the customer was actually charged, frozen at purchase time. This is essential for invoice generation, return calculations, and financial reconciliation. | ✅ Retained — Deliberate Snapshot |
| 7 | `customer_feedbacks` | `name`, `email` | Duplicates `auth_user.first_name + last_name` and `auth_user.email` for logged-in users | **Anonymous submission support.** `user_id` is Nullable to allow guest/anonymous feedback. `name` and `email` are required for all submissions (including guests) so that admin can respond. For logged-in users they are pre-filled but stored independently to preserve the submission record if the account is later deleted. | ✅ Retained — Guest Support & Audit |

---

### Clarification: `order_items` Composite PK & Partial Dependency

In strict 3NF analysis, `product_name` and `price` in `order_items` appear to violate **2NF** because they seem to depend only on `product_id` (part of the composite key), not the full `(order_number, product_id)` key.

**Why this is not a real violation here:**

> The `product_name` and `price` stored in `order_items` are **not the current product name or price from the catalog**. They are **point-in-time values captured at checkout**. Because they can differ per order for the same product, they are functionally dependent on the full composite key `(order_number, product_id)`, not on `product_id` alone.

This is a standard e-commerce design pattern used by platforms such as Shopify, WooCommerce, and Amazon to ensure immutable order history.

---

### Summary

> The schema is in **3NF**, with **intentional denormalization** in `orders` (financial and address snapshots) and `order_items` (price and product name snapshots) to preserve historical accuracy, support invoice generation, and maintain an immutable audit trail — consistent with standard e-commerce database design practice.

---

## 🎓 Viva & Project Defense Guide

### 1. The Core Viva Statement
If the examiner asks: *"Is your database normalized to 3NF?"*
> **Answer:**
> *"The SoundSphere database is designed to satisfy 1NF, 2NF, and 3NF by keeping all attribute values atomic, eliminating repeating groups, and separating independent business entities into distinct relational tables. Some point-in-time snapshot fields are intentionally retained in orders and order items to preserve immutable historical transaction data and support financial invoice integrity."*

### 2. Why `auth_user` retains its standard `id PK` with `username UNIQUE`
- `auth_user` is Django's built-in, industry-standard authentication model.
- `id` (Auto-Increment Integer) is the surrogate **Primary Key** optimized for fast foreign-key indexing and database joins across tables.
- `username` is a **Natural Alternate Key (Candidate Key)** with a `UNIQUE` constraint to guarantee unique login credentials.
- Changing `auth_user.id` to a string natural key would break core Django middleware, session authentication, and foreign key performance across the framework.

### 3. Understanding `UNIQUE ≠ Redundant Primary Key`
In relational theory, a table can have multiple **Candidate Keys**. The database architect designates one as the **Primary Key** (for internal row identification and indexing) while applying `UNIQUE` constraints to the remaining candidate keys (for business integrity).
- **`products` (`id PK`, `slug UNIQUE`)**: `id` provides integer join efficiency; `slug` guarantees SEO-friendly URL uniqueness without requiring expensive multi-byte string joins.
- **`orders` (`order_number PK` or `order_number UNIQUE`)**: Identifies orders with a customer-facing tracking format (e.g. `SS-A1B2C3D4`).
- **`payments` (`id PK`, `transaction_id UNIQUE`)**: `transaction_id` is an external payment gateway reference that must be unique to prevent replay attacks, while `id` identifies the internal database record.

### 4. Why `order_items` snapshots are essential (Not a Normalization Flaw)
- If `order_items` dynamically read `product.name` and `product.price` from the `products` table, any catalog update (e.g. price change from ₹1,999 to ₹2,499 or product title rebrand) would retroactively distort past customer orders and tax invoices.
- Capturing `product_name` and `price` at checkout freezes the exact transaction state. In relational analysis, these values depend on the purchase event itself, making them valid point-in-time attributes.
