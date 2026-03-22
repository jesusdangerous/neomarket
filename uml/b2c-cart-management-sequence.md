```mermaid
sequenceDiagram

participant Customer as "Покупатель (клиент) "

participant Cart as "Корзина (openapi1.yaml) "

participant Catalog as "B2C Каталог (openapi2.yaml) "

Note over Customer, Catalog: Блок 1: Добавление товара в корзину

Customer->>Cart: 1.1 отправляет запрос на добавление товара<br>POST /api/v1/cart/items<br>Заголовки: X-User-Id или X-Session-Id<br>Тело: {sku_id: "7c9e...", quantity: 1}

Cart->>Catalog: 1.2 проверяет существование SKU и остатки<br>GET /api/v1/products/{product_id}/skus/{sku_id}<br>(Note: нужен product_id, которого нет в запросе!)

alt SKU существует

Catalog-->>Cart: 1.3a возвращает данные SKU<br>200 OK<br>Тело: {id, price, quantity, available}

Cart->>Cart: 1.4 проверяет достаточно ли остатков<br>сравнивает requested quantity с available_stock

alt Остатков достаточно

Cart->>Cart: 1.5a добавляет/обновляет позицию в корзине

Cart-->>Customer: 1.6a возвращает успех<br>201 CREATED / 200 OK<br>Тело: {message, item, summary}

else Недостаточно остатков

Cart-->>Customer: 1.5b возвращает ошибку<br>422 Unprocessable Entity<br>Тело: {code: "INSUFFICIENT_STOCK", message: "Доступно только 2"}

end

else SKU не найден

Catalog-->>Cart: 1.3b возвращает 404 Not Found

Cart-->>Customer: 1.4b возвращает ошибку<br>404 Not Found<br>Тело: {code: "SKU_NOT_FOUND"}

end

Note over Customer, Catalog: Блок 2: Просмотр корзины

Customer->>Cart: 2.1 запрашивает содержимое корзины<br>GET /api/v1/cart<br>Заголовки: X-User-Id / X-Session-Id

Cart->>Cart: 2.2 получает список позиций из своей БД

Note over Cart: Для каждой позиции нужно обогатить данными из каталога<br>(batch-запроса в спецификации нет)

loop Для каждой позиции

Cart->>Catalog: 2.3 запрашивает актуальные данные SKU<br>GET /api/v1/products/{product_id}/skus/{sku_id}

Catalog-->>Cart: 2.4 возвращает {price, available_stock}

end

Cart->>Cart: 2.5 рассчитывает итоги (total_amount, line_totals)

Cart-->>Customer: 2.6 возвращает корзину<br>200 OK<br>Тело: {items: [...], summary: {...}, checkout_payload: {...}}

Note over Customer, Catalog: Блок 3: Изменение количества

Customer->>Cart: 3.1 отправляет запрос на изменение<br>PUT /api/v1/cart/items/{item_id}<br>Тело: {quantity: 3}

Cart->>Catalog: 3.2 проверяет актуальные остатки SKU

Catalog-->>Cart: 3.3 возвращает available_stock

alt Остатков достаточно

Cart->>Cart: 3.4a обновляет количество

Cart-->>Customer: 3.5a возвращает обновлённую позицию<br>200 OK

else Недостаточно

Cart-->>Customer: 3.4b возвращает 422

end

Note over Customer, Catalog: Блок 4: Валидация корзины

Customer->>Cart: 4.1 запрашивает валидацию корзины<br>GET /cart/validate<br>Заголовок: Authorization

Cart->>Catalog: 4.2 для каждой позиции проверяет актуальность

Catalog-->>Cart: 4.3 возвращает статусы товаров

Cart->>Cart: 4.4 формирует список проблем (issues)

Cart-->>Customer: 4.5 возвращает результат валидации<br>200 OK<br>Тело: {is_valid, can_checkout, issues: [...]}

Note over Customer, Catalog: Блок 5: Очистка корзины

Customer->>Cart: 5.1 отправляет запрос на очистку<br>DELETE /api/v1/cart<br>Заголовки: X-User-Id / X-Session-Id

Cart->>Cart: 5.2 удаляет все позиции

Cart-->>Customer: 5.3 возвращает 204 No Content