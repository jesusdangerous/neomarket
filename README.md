# NeoMarket

Initial implementation bootstrap for Django microservices.

## Implemented in this step

- Added microservice skeletons:
	- `services/catalog`
	- `services/cart`
	- `services/orders`
	- `services/moderation`
- Added web frontend:
	- `frontend` (single UI for storefront + orders + moderation)
- Added shared local infrastructure:
	- `docker-compose.yml`
	- `infra/postgres/init-multiple-dbs.sql`
- Added baseline Django + DRF + OpenAPI docs endpoint in each backend service.

## Services and Ports

- Catalog service: `http://localhost:8001`
- Cart service: `http://localhost:8002`
- Orders service: `http://localhost:8003`
- Moderation service: `http://localhost:8004`
- Frontend (unified UI): `http://localhost:8080`

Health endpoints:

- `GET /health/`

Schema/docs endpoints:

- `GET /api/schema/`
- `GET /api/docs/`

## Quick Start

1. Build and run containers:

	 ```bash
	 docker compose up --build
	 ```

2. In another terminal, run migrations for each service:

	 ```bash
	 docker compose exec catalog python manage.py migrate
	 docker compose exec cart python manage.py migrate
	 docker compose exec orders python manage.py migrate
	 docker compose exec moderation python manage.py migrate
	 ```

3. Verify health:

	 ```bash
	 curl http://localhost:8001/health/
	 curl http://localhost:8002/health/
	 curl http://localhost:8003/health/
	 curl http://localhost:8004/health/
	 ```

## Current Architecture Scope

- Contract-first implementation path based on:
	- `b2c/catalog/openapi.yaml`
	- `b2c/cart/openapi.yaml`
	- `b2c/orders/openapi.yaml`
- PostgreSQL for service databases.
- Redis reserved for cache/Celery broker.
- Celery integration is prepared by dependencies and environment variables; domain tasks will be added in the next iteration.

## Current Catalog Progress

- Implemented models:
	- Category
	- Product
	- Sku
- Implemented read endpoints:
	- `GET /api/v1/products`
	- `GET /api/v1/products/{id}`
	- `GET /api/v1/products/{id}/similar`
	- `GET /api/v1/products/{product_id}/skus`
	- `GET /api/v1/products/{product_id}/skus/{sku_id}`
	- `GET /api/v1/categories`
	- `GET /api/v1/categories/{id}`
	- `GET /api/v1/categories/{id}/filters`

## Current Cart Progress

- Implemented models:
	- Cart
	- CartItem
	- Favorite
	- Subscription
- Implemented endpoints:
	- `GET /api/v1/cart`
	- `DELETE /api/v1/cart`
	- `POST /api/v1/cart/items`
	- `GET /api/v1/cart/items/{item_id}`
	- `PUT /api/v1/cart/items/{item_id}`
	- `DELETE /api/v1/cart/items/{item_id}`
	- `GET /api/v1/cart/validate`
	- `GET /api/v1/favorites`
	- `POST /api/v1/favorites/{product_id}`
	- `DELETE /api/v1/favorites/{product_id}`
	- `POST /api/v1/favorites/{product_id}/subscribe`
- Integration hardening in Cart:
	- supports `Authorization: Bearer <jwt>` payload parsing for `user_id`
	- keeps `X-User-Id` and `X-Session-Id` fallback for backward compatibility

## Current Moderation Progress

- Implemented models:
	- BlockingReason
	- ModerationCard
	- ModerationEvent (outbox prototype)
- Implemented endpoints:
	- `POST /api/v1/product-moderation/get-next`
	- `POST /api/v1/products/{id}/approve`
	- `POST /api/v1/products/{id}/decline`
	- `GET /api/v1/product-blocking-reasons`
	- `POST /api/v1/product-moderation/enqueue` (temporary bootstrap endpoint before event bus)
- Added protocol spec:
	- `moderation/openapi.yaml`

## Current Frontend Progress

- Added unified UI in `frontend/`:
	- storefront (catalog browsing, add to cart, favorites)
	- cart panel and checkout trigger
	- orders history
	- moderation dashboard (get-next, approve, decline, enqueue)
- Frontend proxies requests to all backend services via nginx.

## Current Orders Progress

- Implemented models:
	- Order
	- OrderItem
	- IdempotencyKey
- Implemented endpoints:
	- `POST /api/v1/orders`
	- `GET /api/v1/orders`
	- `GET /api/v1/orders/{order_id}`
	- `POST /api/v1/orders/{order_id}/cancel`
	- `PATCH /api/v1/orders/{order_id}/status`
- Implemented order status transition policy:
	- `PENDING -> PAID -> ASSEMBLING -> SHIPPED -> DELIVERED`
	- cancel allowed from `PENDING`, `PAID`, `ASSEMBLING`
- Implemented idempotency support for create order:
	- request header `Idempotency-Key`
- Integration hardening in Orders:
	- supports `Authorization: Bearer <jwt>` payload parsing for `user_id` and admin role
	- validates cart via Cart service before order creation

## Automated Tests

- Cart API tests:
	- identity requirement check
	- add/get cart item flow with JWT
	- favorites authorization check
- Orders API tests:
	- create-order idempotency via `Idempotency-Key`
	- invalid status transition returns `409`

## Contract and Smoke Commands

- Run contract + API tests for all services:
	- `docker compose run --rm catalog python manage.py test catalog_api`
	- `docker compose run --rm cart python manage.py test cart_api`
	- `docker compose run --rm orders python manage.py test orders_api`
	- `docker compose run --rm moderation python manage.py test moderation_api`
- Run smoke e2e script against running stack:
	- `pwsh ./scripts/smoke_e2e.ps1`

## OpenAPI Quality Notes

- API views now use explicit `operation_id` annotations to avoid collisions.
- Serializer method fields include explicit type hints to improve schema inference.
- Contract schema tests for catalog/cart/orders pass on dockerized runs.

## Quick UI Flow

1. Open `http://localhost:8080`.
2. In `Storefront`, pick SKU and add products to cart.
3. Click `Оформить заказ` to create an order from cart snapshot data.
4. Switch to `Moderation`, enqueue a product or use enqueue buttons from product cards.
5. Take next moderation card and approve/decline it.

## Next Implementation Step

- Integration hardening:
	- replace JWT payload parsing with full signature verification middleware
	- switch moderation enqueue from manual endpoint to real event bus consumer
	- synchronize moderation decisions with B2B product status updates

