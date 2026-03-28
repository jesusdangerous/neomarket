param(
    [string]$UserId = "11111111-1111-1111-1111-111111111111",
    [string]$SkuId = "22222222-2222-2222-2222-222222222222",
    [string]$ProductId = "33333333-3333-3333-3333-333333333333"
)

$ErrorActionPreference = "Stop"

Write-Host "[smoke] Running cart -> orders flow"

$cartHeaders = @{ "X-User-Id" = $UserId }

$addBody = @{ sku_id = $SkuId; quantity = 1 } | ConvertTo-Json
$addResp = Invoke-RestMethod -Method Post -Uri "http://localhost:8002/api/v1/cart/items" -Headers $cartHeaders -Body $addBody -ContentType "application/json"
Write-Host "[smoke] Added cart item: $($addResp.item_id)"

$validateResp = Invoke-RestMethod -Method Get -Uri "http://localhost:8002/api/v1/cart/validate" -Headers $cartHeaders
if (-not $validateResp.can_checkout) {
    throw "Cart is not ready for checkout"
}
Write-Host "[smoke] Cart validation passed"

$orderHeaders = @{ "X-User-Id" = $UserId; "Idempotency-Key" = [guid]::NewGuid().ToString() }
$orderBody = @{
    items = @(
        @{
            product_id = $ProductId
            sku_id = $SkuId
            quantity = 1
            unit_price = @{ amount = 10000; currency = "RUB" }
            line_total = @{ amount = 10000; currency = "RUB" }
        }
    )
    total = @{ amount = 10000; currency = "RUB" }
    delivery_address = @{
        city = "Moscow"
        street = "Tverskaya"
        house = "1"
        recipient_name = "Smoke User"
        recipient_phone = "+79990000000"
    }
    payment_method = "CARD_ONLINE"
} | ConvertTo-Json -Depth 6

$orderResp = Invoke-RestMethod -Method Post -Uri "http://localhost:8003/api/v1/orders" -Headers $orderHeaders -Body $orderBody -ContentType "application/json"
Write-Host "[smoke] Created order: $($orderResp.id)"

$orderGetResp = Invoke-RestMethod -Method Get -Uri "http://localhost:8003/api/v1/orders/$($orderResp.id)" -Headers @{ "X-User-Id" = $UserId }
Write-Host "[smoke] Loaded order status: $($orderGetResp.status)"

Write-Host "[smoke] OK"
