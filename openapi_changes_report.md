# OpenAPI Changes Report

Документ фиксирует доработки 4 OpenAPI файлов для снижения рисков при разработке и интеграции.

## Измененные файлы

- `b2b/openapi.yaml`
- `b2c/orders/openapi.yaml`
- `b2c/cart/openapi.yaml`
- `b2c/catalog/openapi.yaml`

## Что добавлено и зачем

### 1) `b2b/openapi.yaml`

Что было:
- Часть контрактов была заглушками (`type: object` без структуры).
- Была внешняя ссылка на отсутствующий файл схем (`../shared/schemas.yaml`).
- Не хватало общих ошибок, параметров и нормализованных response-компонентов.

Что добавлено:
- Полный набор схем:
  - `Product`, `Sku`, `Invoice`
  - request-схемы: `CreateProductRequest`, `UpdateProductRequest`, `CreateSkuRequest`, `UpdateSkuRequest`, `CreateInvoiceRequest`, `AcceptInvoiceRequest`
  - вспомогательные: `Category`, `Image`, `Characteristic`, `InvoiceItem`
  - `ErrorResponse`
- Переиспользуемые `components/responses` (`BadRequest`, `Unauthorized`, `NotFound`).
- Параметр `ProductId` в `components/parameters`.
- Единый `BearerAuth`, теги и `servers`.
- Новый endpoint листинга: `GET /api/v1/products` с пагинацией и фильтрами (`limit`, `offset`, `category_id`, `status`, `search`).
- Схема ответа списка: `ProductListResponse`.

Зачем:
- Исключить ambiguity при backend/frontend разработке.
- Убрать битые `$ref`, которые ломают генерацию клиентов и валидаторы.
- Зафиксировать однозначный контракт для CRUD операций.

### 2) `b2c/orders/openapi.yaml`

Что было:
- Файл почти пустой (`paths: {}`), без рабочих endpoint-ов и схем.

Что добавлено:
- Endpoints:
  - `POST /api/v1/orders` — создание заказа
  - `GET /api/v1/orders` — история заказов
  - `GET /api/v1/orders/{order_id}` — получение заказа
  - `POST /api/v1/orders/{order_id}/cancel` — отмена
  - `PATCH /api/v1/orders/{order_id}/status` — смена статуса
- Схемы:
  - `Order`, `OrderItem`, `OrderListResponse`
  - `CreateOrderRequest`, `CancelOrderRequest`, `UpdateOrderStatusRequest`
  - `Money`, `DeliveryAddress`, `OrderStatus`, `ErrorResponse`
- Общие responses и security scheme.

Зачем:
- Дать команде полноценный контракт заказов для разработки без «додумывания».
- Зафиксировать state machine статусов и типовые ошибки интеграции.

### 3) `b2c/cart/openapi.yaml`

Что было:
- Конфликт идентификации пользователя:
  - в некоторых endpoint использовался JWT,
  - но одновременно требовался `user_id` в query.
- В ответах для подборок использовались ссылки на `#/components/schemas/Error`, а остальная схема работала с `ErrorResponse`.

Что исправлено:
- Удалены `user_id` query-параметры из `favorites` mutation endpoint-ов.
- В трех ответах заменены ссылки `#/components/schemas/Error` на `#/components/schemas/ErrorResponse`.

Зачем:
- Устранить противоречие контракта авторизации (JWT vs query user_id).
- Привести формат ошибок к единому типу, чтобы не ломать SDK и фронтовые error-handlers.

### 4) `b2c/catalog/openapi.yaml`

Что было:
- Опечатка в enum статуса товара: `ON_MODERATED` (несовместимо с остальными схемами).
- `ErrorResponse` не имел обязательных полей (`required`).

Что исправлено:
- `ProductStatus.enum` исправлен на:
  - `CREATED`, `ON_MODERATION`, `MODERATED`, `BLOCKED`
- В `ErrorResponse` добавлено `required: [message]`.
- Поле остатков SKU унифицировано: `quantity` -> `active_quantity`.

### 5) Дополнительная унификация `b2c/cart/openapi.yaml`

Что исправлено:
- Поле остатка товара в корзине унифицировано: `available_stock` -> `active_quantity`.

Зачем:
- Свести к минимуму ошибки маппинга между B2B/B2C-контрактами при резервах и проверке остатков.

Зачем:
- Обеспечить единый словарь статусов между сервисами.
- Сделать контракт ошибок валидируемым и предсказуемым.

## Результат для разработки

- Убраны критические блокеры генерации клиентов (`$ref` на отсутствующие схемы).
- Закрыты пустые зоны контракта в `orders` и `b2b`.
- Снижены риски интеграционных ошибок между B2B/B2C/Frontend.
- Контракты стали более строгими и пригодными для контрактного тестирования.
