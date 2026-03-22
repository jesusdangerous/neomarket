```mermaid
sequenceDiagram

participant Customer as "Покупатель (клиент) "

participant Favorite as "Избранное (openapi1.yaml) "

participant Catalog as "B2C Каталог (openapi2.yaml) "

Note over Customer, Catalog: Блок 1: Добавление в избранное

Customer->>Favorite: 1.1 отправляет запрос на добавление в избранное<br>POST /api/v1/favorites/{product_id}?user_id={user_id}

Favorite->>Catalog: 1.2 проверяет существование товара<br>GET /api/v1/products/{product_id}

alt Товар существует

Catalog-->>Favorite: 1.3a возвращает товар<br>200 OK

Favorite->>Favorite: 1.4a проверяет, нет ли уже в избранном

alt Уже есть

Favorite-->>Customer: 1.5a(i) возвращает 200 (уже было)

else Нет

Favorite->>Favorite: 1.5a(ii) сохраняет в избранное

Favorite-->>Customer: 1.6a(ii) возвращает 201 Created

end

else Товар не найден

Catalog-->>Favorite: 1.3b возвращает 404

Favorite-->>Customer: 1.4b возвращает 404 Not Found

end

Note over Customer, Catalog: Блок 2: Получение списка избранного

Customer->>Favorite: 2.1 запрашивает список избранного<br>GET /api/v1/favorites?limit=20&offset=0&user_id={user_id}

Favorite->>Favorite: 2.2 получает список product_id из БД

Note over Favorite: batch-запроса нет, нужен поход за каждым товаром

loop Для каждого product_id

Favorite->>Catalog: 2.3 запрашивает данные товара<br>GET /api/v1/products/{product_id}

alt Товар доступен

Catalog-->>Favorite: 2.4a возвращает товар

else Товар недоступен (удалён/заблокирован)

Catalog-->>Favorite: 2.4b 404 или 403

Note over Favorite: исключает товар из ответа

end

end

Favorite->>Favorite: 2.5 сортирует по дате добавления

Favorite-->>Customer: 2.6 возвращает список<br>200 OK<br>Тело: {items: [{product: {...}, added_at}], total: 5}

Note over Customer, Catalog: Блок 3: Удаление из избранного

Customer->>Favorite: 3.1 отправляет запрос на удаление<br>DELETE /api/v1/favorites/{product_id}?user_id={user_id}

Favorite->>Favorite: 3.2 удаляет запись из БД

Favorite-->>Customer: 3.3 возвращает 204 No Content

Note over Customer, Catalog: Блок 4: Подписка на уведомления

Customer->>Favorite: 4.1 отправляет запрос на подписку<br>POST /api/v1/favorites/{product_id}/subscribe<br>Тело: {notify_on: ["IN_STOCK", "PRICE_DOWN"]}

Favorite->>Catalog: 4.2 проверяет существование товара<br>GET /api/v1/products/{product_id}

alt Товар существует

Catalog-->>Favorite: 4.3a возвращает товар

Favorite->>Favorite: 4.4a проверяет, нет ли уже подписки

alt Уже есть

Favorite-->>Customer: 4.5a(i) возвращает 409 Conflict

else Нет

Favorite->>Favorite: 4.5a(ii) сохраняет подписку

Favorite-->>Customer: 4.6a(ii) возвращает 201 Created<br>Тело: {id, product, notify_on, created_at}

end

else Товар не найден

Catalog-->>Favorite: 4.3b возвращает 404

Favorite-->>Customer: 4.4b возвращает 404

end