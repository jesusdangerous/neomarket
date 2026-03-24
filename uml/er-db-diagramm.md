erDiagram

%% =========================
%% B2B (Seller Cabinet)
%% =========================

PRODUCTS {
    UUID id PK
    UUID seller_id
    TEXT title
    TEXT description
    UUID category_id FK
    TEXT status
    TEXT slug
    TIMESTAMP created_at
    TIMESTAMP updated_at
}

CATEGORIES {
    UUID id PK
    TEXT name
    TEXT slug
    UUID parent_id FK
    BOOLEAN is_active
    TIMESTAMP created_at
    TIMESTAMP updated_at
}

PRODUCT_IMAGES {
    UUID id PK
    UUID product_id FK
    TEXT url
    INT ordering
}

CHARACTERISTICS {
    UUID id PK
    TEXT name
}

PRODUCT_CHARACTERISTICS {
    UUID id PK
    UUID product_id FK
    UUID characteristic_id FK
    TEXT value
}

SKUS {
    UUID id PK
    UUID product_id FK
    TEXT name
    BIGINT price
    INT active_quantity
    TEXT status
    TIMESTAMP created_at
    TIMESTAMP updated_at
}

SKU_CHARACTERISTICS {
    UUID id PK
    UUID sku_id FK
    UUID characteristic_id FK
    TEXT value
}

SKU_IMAGES {
    UUID id PK
    UUID sku_id FK
    TEXT url
    INT ordering
}

INVOICES {
    UUID id PK
    UUID seller_id
    TEXT status
    TIMESTAMP created_at
}

INVOICE_ITEMS {
    UUID id PK
    UUID invoice_id FK
    UUID sku_id FK
    INT quantity
}

RESERVATIONS {
    UUID id PK
    UUID sku_id FK
    INT quantity
    TIMESTAMP expires_at
    TEXT status
    TIMESTAMP created_at
}

SKU_PRICE_HISTORY {
    UUID id PK
    UUID sku_id FK
    BIGINT price
    TIMESTAMP created_at
}

%% =========================
%% B2C (Customer side)
%% =========================

USERS {
    UUID id PK
}

FAVORITES {
    UUID id PK
    UUID user_id FK
    UUID product_id FK
    TIMESTAMP added_at
}

CARTS {
    UUID id PK
    UUID user_id FK
}

CART_ITEMS {
    UUID id PK
    UUID cart_id FK
    UUID sku_id
    INT quantity
    TIMESTAMP created_at
}

ORDERS {
    UUID id PK
    UUID user_id FK
    TEXT status
    BIGINT total_amount
    TIMESTAMP created_at
}

ORDER_ITEMS {
    UUID id PK
    UUID order_id FK
    UUID sku_id
    INT quantity
    BIGINT price
}

SUBSCRIPTIONS {
    UUID id PK
    UUID user_id FK
    UUID product_id FK
    TEXT notify_on
    TIMESTAMP created_at
}

%% =========================
%% CMS / Home / Marketing
%% =========================

BANNERS {
    UUID id PK
    TEXT title
    TEXT image_url
    TEXT link
    INT priority
}

BANNER_EVENTS {
    UUID id PK
    UUID banner_id FK
    TEXT event_type
    TIMESTAMP created_at
}

COLLECTIONS {
    UUID id PK
    TEXT title
    TEXT description
    TEXT cover_image_url
    TEXT target_url
    INT priority
    DATE start_date
}

COLLECTION_PRODUCTS {
    UUID id PK
    UUID collection_id FK
    UUID product_id FK
}

%% =========================
%% RELATIONS
%% =========================

CATEGORIES ||--o{ PRODUCTS : "has"
CATEGORIES ||--o{ CATEGORIES : "parent"

PRODUCTS ||--o{ PRODUCT_IMAGES : "has"
PRODUCTS ||--o{ PRODUCT_CHARACTERISTICS : "has"
PRODUCTS ||--o{ SKUS : "has"

SKUS ||--o{ SKU_CHARACTERISTICS : "has"
SKUS ||--o{ SKU_IMAGES : "has"
SKUS ||--o{ INVOICE_ITEMS : "in"
SKUS ||--o{ RESERVATIONS : "reserved"
SKUS ||--o{ SKU_PRICE_HISTORY : "price history"

CHARACTERISTICS ||--o{ PRODUCT_CHARACTERISTICS : "used_in"
CHARACTERISTICS ||--o{ SKU_CHARACTERISTICS : "used_in"

INVOICES ||--o{ INVOICE_ITEMS : "contains"

USERS ||--o{ FAVORITES : "has"
PRODUCTS ||--o{ FAVORITES : "liked"

USERS ||--o{ CARTS : "owns"
CARTS ||--o{ CART_ITEMS : "contains"

USERS ||--o{ ORDERS : "places"
ORDERS ||--o{ ORDER_ITEMS : "contains"

PRODUCTS ||--o{ SUBSCRIPTIONS : "subscribed"

BANNERS ||--o{ BANNER_EVENTS : "tracked"

COLLECTIONS ||--o{ COLLECTION_PRODUCTS : "contains"
PRODUCTS ||--o{ COLLECTION_PRODUCTS : "in"