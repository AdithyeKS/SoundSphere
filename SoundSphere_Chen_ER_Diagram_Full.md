# SoundSphere - Full Entity-Relationship Diagram (Chen Model)

This document provides a detailed breakdown of the complete SoundSphere E-Commerce Entity-Relationship Diagram designed using the classic **Peter Chen ER Notation**. This diagram accurately reflects all tables and structures from the `SoundSphere_Database_Design.md` database schema.

## 📁 Diagram File
The diagram has been generated in a standard Draw.io XML format. You can open and edit it using [diagrams.net](https://app.diagrams.net/) or any compatible offline Draw.io editor.
- **File Path:** [SoundSphere_Chen_ER_Diagram_Full.xml](file:///d:/SoundSphere/SoundSphere_Chen_ER_Diagram_Full.xml)

*(Looking for the simpler, high-level version? See [SoundSphere_Chen_ER_Diagram.xml](file:///d:/SoundSphere/SoundSphere_Chen_ER_Diagram.xml))*

---

## 🏗️ Chen ER Model Constructs Used

1. **Entities (Rectangles):** Core objects in the system. Strong entities have standard rectangles, while Weak entities (dependent on another entity, e.g., `CART_ITEM` and `ORDER_ITEM`) have double rectangles.
2. **Relationships (Diamonds):** Interactions or links between entities. Strong relationships use standard diamonds, while Identifying relationships (connecting a strong to a weak entity) use double diamonds.
3. **Attributes (Ellipses):** Properties of an entity. 
   - **Key Attributes:** Underlined text inside the ellipse (e.g., `id`).
   - **Derived Attributes:** Dashed ellipses (e.g., `discount_price`, `total_amount`).
4. **Cardinalities:** Edges connect these elements and are labeled `1`, `N`, or `M` to show mapping constraints.

---

## 📊 Complete ER Model Breakdown

### 1. Entities & Their Key Attributes

#### Strong Entities:
*   **USER**: Core authentication record. 
    *   Key: `id` (Underlined)
    *   Attributes: `username`, `email`
*   **USER_PROFILE**: Extended customer details.
*   **SELLER_PROFILE**: Store and seller application data.
*   **SHIPPING_ADDRESS**: Delivery location details.
*   **CATEGORY**: Product groupings.
*   **PRODUCT**: Headphone catalog item.
    *   Key: `id` (Underlined)
    *   Attributes: `name`, `price`, `stock`, `discount_price` (Derived)
*   **REVIEW**: Customer feedback on products.
*   **CART**: Active shopping session.
*   **ORDER**: Finalized purchase record.
    *   Key: `id` (Underlined)
    *   Attributes: `status`, `total_amount` (Derived)
*   **PAYMENT**: Transaction record.
    *   Key: `id` (Underlined)
    *   Attributes: `payment_method`
*   **WISHLIST**: Saved products.

#### Weak Entities:
*   **CART_ITEM**: Exists only within a specific CART.
    *   Partial Key / Attribute: `quantity`
*   **ORDER_ITEM**: Exists only within a specific ORDER.

---

### 2. Relationships & Cardinalities

| Entity 1 | Cardinality | Relationship (Diamond) | Cardinality | Entity 2 | Notes |
| :--- | :---: | :--- | :---: | :--- | :--- |
| **USER** | 1 | `HAS_PROFILE` | 1 | **USER_PROFILE** | One-to-One extension |
| **USER** | 1 | `MANAGES_STORE` | 0..1 | **SELLER_PROFILE** | Optional One-to-One |
| **USER** | 1 | `HAS_ADDRESS` | N | **SHIPPING_ADDRESS** | One User, Many Addresses |
| **SELLER_PROFILE** | 1 | `SELLS` | N | **PRODUCT** | One Seller, Many Products |
| **CATEGORY** | 1 | `BELONGS_TO` | N | **PRODUCT** | One Category, Many Products |
| **USER** | 1 | `WRITES` | N | **REVIEW** | One User, Many Reviews |
| **PRODUCT** | 1 | `HAS_REVIEW` | N | **REVIEW** | One Product, Many Reviews |
| **USER** | 1 | `HAS_CART` | 1 | **CART** | One-to-One Session |
| **CART** | 1 | `CONTAINS` *(Double)* | N | **CART_ITEM** *(Double)* | Identifying Weak Relationship |
| **PRODUCT** | 1 | `ITEM_OF` | N | **CART_ITEM** | Product mapping for cart |
| **USER** | 1 | `PLACES` | N | **ORDER** | One User, Many Orders |
| **ORDER** | 1 | `INCLUDES` *(Double)*| N | **ORDER_ITEM** *(Double)*| Identifying Weak Relationship |
| **PRODUCT** | 1 | `REFERS_TO` | N | **ORDER_ITEM** | Product mapping for order |
| **ORDER** | 1 | `PAID_VIA` | 1 | **PAYMENT** | One Order, One Payment |
| **USER** | 1 | `HAS_WISHLIST` | 1 | **WISHLIST** | One-to-One Wishlist |

---

## 🎨 Diagram Representation
The created Draw.io diagram visually maps these components with specific coloring:
- **Entities:** Blue / Yellow / Pink / Green / Purple solid rectangles.
- **Relationships:** Colored Diamonds matching their functional domain.
- **Attributes:** Connected Ellipses with primary keys strictly underlined.
- **Weak Relationships & Entities:** Clearly designated with Double-lines (`shape=ext;double=1` and `shape=rhombus;double=1`).
