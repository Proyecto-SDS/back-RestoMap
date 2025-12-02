# SCRIPT DE TESTING - Dashboard Mesero
# Testing con PowerShell en Windows

$API_URL = "http://localhost:5000"
$BEARER_TOKEN = "your-token-here"  # Reemplazar con token real

Write-Host "=================================" -ForegroundColor Cyan
Write-Host "Testing Dashboard Mesero API" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# 1. CREAR UN PEDIDO
# ============================================================================
Write-Host "1. POST /api/pedidos/ - Crear pedido" -ForegroundColor Yellow

$body = @{
    localId = "1"
    mesaNumero = "Mesa 5"
    items = @(
        @{
            productoId = "1"
            cantidad = 2
            precio = 9500
            comentario = "Sin cebolla"
        },
        @{
            productoId = "3"
            cantidad = 1
            precio = 7800
            comentario = ""
        }
    )
    total = 26800
} | ConvertTo-Json

Write-Host "Request:" -ForegroundColor Green
Write-Host $body

Write-Host ""
Write-Host "Ejecutando..." -ForegroundColor Green

try {
    $response = Invoke-WebRequest -Uri "$API_URL/api/pedidos/" `
        -Method POST `
        -Body $body `
        -ContentType "application/json"
    
    Write-Host "Status Code: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "Response:" -ForegroundColor Green
    Write-Host ($response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10)
    
    $pedidoId = ($response.Content | ConvertFrom-Json).id
    Write-Host "Pedido ID: $pedidoId" -ForegroundColor Yellow
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "---" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# 2. OBTENER DETALLE DEL PEDIDO
# ============================================================================
if ($pedidoId) {
    Write-Host "2. GET /api/pedidos/{id} - Obtener detalle" -ForegroundColor Yellow
    Write-Host "Ejecutando..." -ForegroundColor Green
    
    try {
        $response = Invoke-WebRequest -Uri "$API_URL/api/pedidos/$pedidoId" `
            -Method GET
        
        Write-Host "Status Code: $($response.StatusCode)" -ForegroundColor Green
        Write-Host "Response:" -ForegroundColor Green
        Write-Host ($response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10)
    } catch {
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "---" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# 3. AGREGAR ITEM AL PEDIDO
# ============================================================================
if ($pedidoId) {
    Write-Host "3. POST /api/pedidos/{id}/items - Agregar item" -ForegroundColor Yellow
    
    $body = @{
        productoId = "2"
        cantidad = 1
        observaciones = "Sin picante"
    } | ConvertTo-Json
    
    Write-Host "Request:" -ForegroundColor Green
    Write-Host $body
    Write-Host ""
    Write-Host "Ejecutando..." -ForegroundColor Green
    
    try {
        $response = Invoke-WebRequest -Uri "$API_URL/api/pedidos/$pedidoId/items" `
            -Method POST `
            -Body $body `
            -ContentType "application/json"
        
        Write-Host "Status Code: $($response.StatusCode)" -ForegroundColor Green
        Write-Host "Response:" -ForegroundColor Green
        Write-Host ($response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10)
        
        $itemId = ($response.Content | ConvertFrom-Json).id
        Write-Host "Item ID: $itemId" -ForegroundColor Yellow
    } catch {
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "---" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# 4. ACTUALIZAR ITEM
# ============================================================================
if ($pedidoId -and $itemId) {
    Write-Host "4. PUT /api/pedidos/{id}/items/{cuenta_id} - Actualizar item" -ForegroundColor Yellow
    
    $body = @{
        cantidad = 3
        observaciones = "Sin sal, extra picante"
    } | ConvertTo-Json
    
    Write-Host "Request:" -ForegroundColor Green
    Write-Host $body
    Write-Host ""
    Write-Host "Ejecutando..." -ForegroundColor Green
    
    try {
        $response = Invoke-WebRequest -Uri "$API_URL/api/pedidos/$pedidoId/items/$itemId" `
            -Method PUT `
            -Body $body `
            -ContentType "application/json"
        
        Write-Host "Status Code: $($response.StatusCode)" -ForegroundColor Green
        Write-Host "Response:" -ForegroundColor Green
        Write-Host ($response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10)
    } catch {
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "---" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# 5. ELIMINAR ITEM
# ============================================================================
if ($pedidoId -and $itemId) {
    Write-Host "5. DELETE /api/pedidos/{id}/items/{cuenta_id} - Eliminar item" -ForegroundColor Yellow
    Write-Host "Ejecutando..." -ForegroundColor Green
    
    try {
        $response = Invoke-WebRequest -Uri "$API_URL/api/pedidos/$pedidoId/items/$itemId" `
            -Method DELETE
        
        Write-Host "Status Code: $($response.StatusCode)" -ForegroundColor Green
        Write-Host "Response:" -ForegroundColor Green
        Write-Host ($response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10)
    } catch {
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=================================" -ForegroundColor Cyan
Write-Host "Testing completado" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
