```mermaid
sequenceDiagram

participant Customer as "Покупатель (клиент) "

participant Catalog as "B2C Каталог (openapi2.yaml) "

Note over Customer, Catalog: Блок 1: Получение дерева категорий

Customer->>Catalog: 1.1 запрашивает дерево категорий<br>GET /api/v1/categories<br>Ожидает: 200 OK

Catalog-->>Customer: 1.2 возвращает иерархию категорий<br>200 OK<br>Тело: {items: [{id, name, children: [...]}]}

Note over Customer, Catalog: Блок 2: Выбор категории и фильтры

Customer->>Catalog: 2.1 запрашивает детали категории<br>GET /api/v1/categories/{id}?include_product_count=true<br>Ожидает: 200 OK

Catalog-->>Customer: 2.2 возвращает информацию о категории<br>200 OK<br>Тело: {id, name, description, product_count, seo, ...}

Customer->>Catalog: 2.3 запрашивает доступные фильтры для категории<br>GET /api/v1/categories/{id}/filters<br>Ожидает: 200 OK

Catalog-->>Customer: 2.4 возвращает список фильтров<br>200 OK<br>Тело: {items: [{slug, name, type, values}]}

Note over Customer, Catalog: Блок 3: Поиск и фильтрация товаров

Customer->>Catalog: 3.1 запрашивает список товаров с фильтрацией<br>GET /api/v1/products?category_id=...&filters[brand]=Apple&sort=price_asc&limit=20&offset=0<br>Ожидает: 200 OK

Catalog-->>Customer: 3.2 возвращает список товаров с пагинацией<br>200 OK<br>Тело: {total_count: 150, items: [{id, title, price, ...}]}

Note over Customer, Catalog: Блок 4: Получение фасетов (динамических фильтров)

Customer->>Catalog: 4.1 запрашивает фасеты с подсчётами<br>GET /api/v1/catalog/facets?category_id=...&filters[brand]=Apple<br>Ожидает: 200 OK

Catalog-->>Customer: 4.2 возвращает фасеты с количествами<br>200 OK<br>Тело: {facets: [{name: "brand", values: [{value: "Apple", count: 42}]}]}

Note over Customer, Catalog: Блок 5: Карточка товара

Customer->>Catalog: 5.1 запрашивает полную карточку товара<br>GET /api/v1/products/{id}<br>Ожидает: 200 OK

Catalog-->>Customer: 5.2 возвращает товар с характеристиками и SKU<br>200 OK<br>Тело: {id, title, description, characteristics, skus: [...]}

Customer->>Catalog: 5.3 запрашивает краткий список SKU<br>GET /api/v1/products/{id}/skus<br>Ожидает: 200 OK

Catalog-->>Customer: 5.4 возвращает SKU для отображения в карточке<br>200 OK<br>Тело: [{name, price, image}]

Customer->>Catalog: 5.5 запрашивает детали конкретного SKU<br>GET /api/v1/products/{id}/skus/{sku_id}<br>Ожидает: 200 OK

Catalog-->>Customer: 5.6 возвращает полную информацию о SKU<br>200 OK<br>Тело: {id, name, price, quantity, characteristics, images}