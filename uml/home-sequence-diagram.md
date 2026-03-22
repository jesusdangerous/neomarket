```mermaid
sequenceDiagram

participant Customer as "Покупатель (клиент) "

participant Home as "Главная (openapi1.yaml) "

participant Catalog as "B2C Каталог (openapi2.yaml) "

Note over Customer, Catalog: Блок 1: Загрузка баннеров

Customer->>Home: 1.1 запрашивает баннеры для главной<br>GET /api/v1/home/banners

Home->>Home: 1.2 фильтрует активные баннеры (is_active=true, start_at<=now<=end_at)

Home->>Home: 1.3 сортирует по priority

Home-->>Customer: 1.4 возвращает список баннеров<br>200 OK<br>Тело: {items: [{id, title, image_url, link, priority}], total_count}

Note over Customer, Catalog: Блок 2: Отправка событий аналитики

Customer->>Home: 2.1 отправляет события о показах/кликах<br>POST /api/v1/banner-events<br>Тело: {events: [{banner_id, event: "impression", timestamp}]}

Home->>Home: 2.2 сохраняет события в БД (для будущей аналитики)

Home-->>Customer: 2.3 возвращает 204 No Content

Note over Customer, Catalog: Блок 3: Получение списка подборок

Customer->>Home: 3.1 запрашивает подборки<br>GET /api/v1/main/collections?limit=10&offset=0

Home->>Home: 3.2 фильтрует активные подборки, сортирует по priority

Home-->>Customer: 3.3 возвращает список подборок<br>200 OK<br>Тело: {metadata: {total_count, limit, offset}, collections: [...]}

Note over Customer, Catalog: Блок 4: Товары из подборки

Customer->>Home: 4.1 запрашивает товары подборки<br>GET /api/v1/collections/{collection_id}/products?limit=20

Home->>Home: 4.2 получает список product_id для этой подборки

loop Для каждого product_id

Home->>Catalog: 4.3 запрашивает данные товара<br>GET /api/v1/products/{id}

Catalog-->>Home: 4.4 возвращает товар

end

Home->>Home: 4.5 собирает недоступные ID

Home-->>Customer: 4.6 возвращает товары подборки<br>200 OK<br>Тело: {collection_title, total_products, items: [...], unavailable_ids: [...]}

Note over Customer, Catalog: Блок 5: Рекомендации "похожие товары"

Customer->>Home: 5.1 запрашивает похожие товары<br>GET /api/v1/products/{id}/similar?limit=10

Home->>Home: 5.2 получает ID похожих товаров (из своей логики)

loop Для каждого product_id

Home->>Catalog: 5.3 запрашивает данные товара

end

Home-->>Customer: 5.4 возвращает список похожих товаров<br>200 OK<br>Тело: {items: [...], total}

Note over Customer, Catalog: Блок 6: Рекомендации "покупают вместе"

Customer->>Home: 6.1 запрашивает рекомендации для корзины<br>GET /api/v1/cart/also_bought?limit=10<br>Заголовок: Authorization

Home->>Home: 6.2 получает состав корзины пользователя

alt Корзина не пуста

Home->>Home: 6.3a вычисляет рекомендации на основе истории покупок

Home-->>Customer: 6.4a возвращает ID рекомендованных товаров<br>200 OK<br>Тело: {recommended_product_ids: [...]}

else Корзина пуста

Home-->>Customer: 6.3b возвращает 409 Conflict<br>Тело: {code: "EMPTY_CART"}

end