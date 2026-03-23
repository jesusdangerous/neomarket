```mermaid
erDiagram

    PRODUCTS {
        BIGINT id PK
        TEXT title
        TEXT description
        BIGINT category_id FK
        TEXT status
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    CATEGORIES {
        BIGINT id PK
        TEXT name
        BIGINT parent_id FK
    }

    PRODUCT_IMAGES {
        BIGINT id PK
        BIGINT product_id FK
        TEXT url
        INT ordering
    }

    CHARACTERISTICS {
        BIGINT id PK
        TEXT name
    }

    PRODUCT_CHARACTERISTICS {
        BIGINT id PK
        BIGINT product_id FK
        BIGINT characteristic_id FK
        TEXT value
    }

    SKUS {
        BIGINT id PK
        BIGINT product_id FK
        TEXT name
        BIGINT price
        INT active_quantity
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    SKU_CHARACTERISTICS {
        BIGINT id PK
        BIGINT sku_id FK
        BIGINT characteristic_id FK
        TEXT value
    }

    INVOICES {
        BIGINT id PK
        TEXT status
        TIMESTAMP created_at
    }

    INVOICE_ITEMS {
        BIGINT id PK
        BIGINT invoice_id FK
        BIGINT sku_id FK
        INT quantity
    }

    %% Relations

    CATEGORIES ||--o{ PRODUCTS : "has"
    CATEGORIES ||--o{ CATEGORIES : "parent"

    PRODUCTS ||--o{ PRODUCT_IMAGES : "has"
    PRODUCTS ||--o{ PRODUCT_CHARACTERISTICS : "has"
    PRODUCTS ||--o{ SKUS : "has"

    CHARACTERISTICS ||--o{ PRODUCT_CHARACTERISTICS : "used_in"
    CHARACTERISTICS ||--o{ SKU_CHARACTERISTICS : "used_in"

    SKUS ||--o{ SKU_CHARACTERISTICS : "has"
    SKUS ||--o{ INVOICE_ITEMS : "in"

    INVOICES ||--o{ INVOICE_ITEMS : "contains"