```mermaid
sequenceDiagram

%% УЧАСТНИКИ - только то, что есть в файлах

participant Seller as "Продавец (пользователь кабинета) "

participant B2B as "B2B Кабинет продавца (openapi.yaml) "

participant Moderation as "Moderation (сервис модерации, openapi (1).yaml) "

participant Moderator as "Модератор (сотрудник) "

participant B2C as "B2C Каталог (публичный, openapi2.yaml) "

%% БЛОК 1: СОЗДАНИЕ ТОВАРА ПРОДАВЦОМ

Note over Seller, B2C: БЛОК 1: Продавец создаёт новый товар

Seller->>B2B: 1.1 отправляет запрос на создание товара<br>POST /api/v1/products<br>Тело: {title, description, category_id, images: [...]}<br>Ожидает: 201 CREATED

B2B->>B2B: 1.2 проверяет права продавца (предполагается, что токен уже есть)<br>⚠️ В спецификации нет User Service, поэтому авторизация не описана

B2B->>B2B: 1.3 сохраняет товар в БД со статусом CREATED<br>присваивает id = 42 (integer)

B2B-->>Seller: 1.4 возвращает подтверждение создания<br>201 CREATED<br>Тело: {id: 42, status: "CREATED", created_at: "2026-03-20T10:00:00Z"}

%% БЛОК 2: ОТПРАВКА НА МОДЕРАЦИЮ

Note over B2B, Moderation: БЛОК 2: Уведомление модерации о новом товаре

Note over B2B, Moderation: ⚠️ В спецификациях НЕТ механизма уведомлений между сервисами.<br>Предполагаем, что Moderation периодически опрашивает B2B (polling)

Moderation->>B2B: 2.1 периодически запрашивает товары со статусом CREATED<br>GET /api/v1/products?status=CREATED<br>Ожидает: 200 OK

B2B-->>Moderation: 2.2 возвращает список новых товаров<br>200 OK<br>Тело: [{id: 42, title: "..."}]

Moderation->>B2B: 2.3 запрашивает полные данные конкретного товара<br>GET /api/v1/products/42<br>Ожидает: 200 OK

B2B-->>Moderation: 2.4 возвращает полную карточку товара<br>200 OK<br>Тело: {id:42, title:"iPhone 15 Pro Max", description:"...", skus:[...], status:"CREATED"}

Moderation->>Moderation: 2.5 создаёт снимок товара для проверки<br>сохраняет копию в свою БД (snapshot_id = 101)

%% БЛОК 3: МОДЕРАТОР БЕРЁТ ТОВАР В РАБОТУ

Note over Moderator, Moderation: БЛОК 3: Модератор берёт товар из очереди

Note over Moderator, Moderation: ⚠️ В спецификации Moderation нет авторизации модератора.<br>Предполагаем, что модератор уже аутентифицирован.

Moderator->>Moderation: 3.1 запрашивает следующую карточку из очереди<br>POST /api/v1/product-moderation/get-next<br>Ожидает: 200 OK или 204 No Content

Moderation->>Moderation: 3.2 выбирает товар из очереди (FIFO)

alt Очередь не пуста

Moderation-->>Moderator: 3.3a возвращает карточку товара для проверки<br>200 OK<br>Тело: {product_id: 42, snapshot: {...}, created_at: "2026-03-20T10:05:00Z"}

Moderator->>Moderator: 3.4 изучает товар, принимает решение (одобрить / отклонить)

%% БЛОК 4: ПРИНЯТИЕ РЕШЕНИЯ

Note over Moderator, B2C: БЛОК 4: Модератор выносит вердикт

alt Товар одобрен

Moderator->>Moderation: 4.1 отправляет решение "одобрить"<br>POST /api/v1/products/42/approve<br>Тело: {moderator_comment: "ok"} (опционально)

Moderation->>Moderation: 4.2 сохраняет решение

Note over Moderation, B2B: ⚠️ Нет механизма уведомления B2B о решении.<br>B2B должен сам опрашивать Moderation?

Moderation->>B2B: 4.3 (предполагается) отправляет уведомление об одобрении<br>НО ЭНДПОИНТА В B2B НЕТ!

Note over B2B: ⚠️ B2B не узнаёт о решении автоматически.<br>Статус товара остаётся CREATED.

else Товар отклонён

Moderator->>Moderation: 4.1a отправляет решение "отклонить" с причиной<br>POST /api/v1/products/42/decline<br>Тело: {reason: "некорректные фото", comment: "размытое изображение"}

Moderation->>Moderation: 4.2a сохраняет решение с причиной

Note over Moderation, B2B: ⚠️ Аналогичная проблема - B2B не узнаёт об отклонении

end

else Очередь пуста

Moderation-->>Moderator: 3.3b очередь пуста<br>204 No Content

Note over Moderator: модератор ждёт или проверяет позже

end

%% БЛОК 5: ПУБЛИКАЦИЯ В B2C КАТАЛОГ

Note over B2B, B2C: БЛОК 5: Появление товара в публичном каталоге

Note over B2B, B2C: ⚠️ Нет автоматической синхронизации между B2B и B2C Catalog.<br>Непонятно, как товар попадает в публичный доступ.

Note over B2C: B2C Catalog должен каким-то образом узнавать о товарах со статусом MODERATED.<br>В спецификациях этого нет.

%% БЛОК 6: ПРОВЕРКА РЕЗУЛЬТАТА

Note over Seller, B2C: БЛОК 6: Проверка статуса (спустя время)

Seller->>B2B: 6.1 запрашивает статус своего товара<br>GET /api/v1/products/42<br>Ожидает: 200 OK

B2B-->>Seller: 6.2 возвращает статус (всё ещё CREATED, так как B2B не получил решение модерации)<br>200 OK<br>Тело: {id:42, status:"CREATED", ...}

Note over Seller: Продавец не понимает, почему товар не публикуется<br>⚠️ Нет уведомлений о результате модерации

Покупатель->>B2C: 6.3 пытается найти товар в каталоге<br>GET /api/v1/products/42

alt Товар не опубликован

B2C-->>Покупатель: 6.4a 404 Not Found

else Если каким-то товар попал в B2C

B2C-->>Покупатель: 6.4b 200 OK

end