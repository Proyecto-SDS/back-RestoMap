#!/bin/bash
# SCRIPT DE TESTING - Dashboard Mesero
# Contiene ejemplos de curl para probar todos los endpoints
# Ejecutar: bash test_pedidos.sh

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

API_URL="http://localhost:5000"
BEARER_TOKEN="your-token-here"  # Reemplazar con token real si se necesita

echo -e "${BLUE}=================================="
echo "Testing Dashboard Mesero API"
echo "==================================${NC}\n"

# ============================================================================
# 1. CREAR UN PEDIDO
# ============================================================================
echo -e "${YELLOW}1. POST /api/pedidos/ - Crear pedido${NC}"
echo -e "${GREEN}Request:${NC}"
cat << 'EOF'
{
  "localId": "1",
  "mesaNumero": "Mesa 5",
  "items": [
    {
      "productoId": "1",
      "cantidad": 2,
      "precio": 9500,
      "comentario": "Sin cebolla"
    },
    {
      "productoId": "3",
      "cantidad": 1,
      "precio": 7800,
      "comentario": ""
    }
  ],
  "total": 26800
}
EOF

echo -e "\n${GREEN}Command:${NC}"
echo "curl -X POST http://localhost:5000/api/pedidos/ \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{}'"

echo -e "\n${GREEN}Response esperada (201):${NC}"
echo "{\"pedidoId\": 1, \"id\": 1, \"localId\": \"1\", \"mesaNumero\": \"Mesa 5\", \"estado\": \"abierto\", \"total\": 26800}"

echo -e "\n${BLUE}---${NC}\n"

# ============================================================================
# 2. OBTENER DETALLE DEL PEDIDO
# ============================================================================
echo -e "${YELLOW}2. GET /api/pedidos/{id} - Obtener detalle${NC}"
echo -e "${GREEN}Command:${NC}"
echo "curl http://localhost:5000/api/pedidos/1"

echo -e "\n${GREEN}Response esperada (200):${NC}"
echo "{\"id\": 1, \"local_id\": 1, \"estado\": \"abierto\", \"total\": 26800, \"items\": [...]}"

echo -e "\n${BLUE}---${NC}\n"

# ============================================================================
# 3. OBTENER MIS PEDIDOS (REQUIERE AUTENTICACIÓN)
# ============================================================================
echo -e "${YELLOW}3. GET /api/pedidos/mis-pedidos - Obtener mis pedidos${NC}"
echo -e "${GREEN}Command (con token):${NC}"
echo "curl http://localhost:5000/api/pedidos/mis-pedidos \\"
echo "  -H 'Authorization: Bearer {token}'"

echo -e "\n${GREEN}Response esperada (200):${NC}"
echo "[{\"id\": 1, \"localId\": 1, \"estado\": \"abierto\", \"total\": 26800, \"items_count\": 2}, ...]"

echo -e "\n${BLUE}---${NC}\n"

# ============================================================================
# 4. AGREGAR ITEM AL PEDIDO
# ============================================================================
echo -e "${YELLOW}4. POST /api/pedidos/{id}/items - Agregar item${NC}"
echo -e "${GREEN}Request:${NC}"
cat << 'EOF'
{
  "productoId": "2",
  "cantidad": 1,
  "observaciones": "Sin picante"
}
EOF

echo -e "\n${GREEN}Command:${NC}"
echo "curl -X POST http://localhost:5000/api/pedidos/1/items \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{...}'"

echo -e "\n${GREEN}Response esperada (201):${NC}"
echo "{\"id\": 3, \"producto_id\": 2, \"producto_nombre\": \"Salmón Grillado\", \"precio_unitario\": 24000, \"cantidad\": 1, \"subtotal\": 24000, \"observaciones\": \"Sin picante\"}"

echo -e "\n${BLUE}---${NC}\n"

# ============================================================================
# 5. ACTUALIZAR ITEM
# ============================================================================
echo -e "${YELLOW}5. PUT /api/pedidos/{id}/items/{cuenta_id} - Actualizar item${NC}"
echo -e "${GREEN}Request:${NC}"
cat << 'EOF'
{
  "cantidad": 3,
  "observaciones": "Sin sal, extra picante"
}
EOF

echo -e "\n${GREEN}Command:${NC}"
echo "curl -X PUT http://localhost:5000/api/pedidos/1/items/1 \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{...}'"

echo -e "\n${GREEN}Response esperada (200):${NC}"
echo "{\"id\": 1, \"producto_id\": 1, \"producto_nombre\": \"Lomo a lo Pobre\", \"precio_unitario\": 9500, \"cantidad\": 3, \"subtotal\": 28500, \"observaciones\": \"Sin sal, extra picante\"}"

echo -e "\n${BLUE}---${NC}\n"

# ============================================================================
# 6. ELIMINAR ITEM
# ============================================================================
echo -e "${YELLOW}6. DELETE /api/pedidos/{id}/items/{cuenta_id} - Eliminar item${NC}"
echo -e "${GREEN}Command:${NC}"
echo "curl -X DELETE http://localhost:5000/api/pedidos/1/items/2"

echo -e "\n${GREEN}Response esperada (200):${NC}"
echo "{\"mensaje\": \"Item eliminado exitosamente\", \"nuevo_total\": 28500}"

echo -e "\n${BLUE}---${NC}\n"

# ============================================================================
# EJEMPLOS EN PYTHON
# ============================================================================
echo -e "${YELLOW}Ejemplos en Python (usando requests):${NC}"

cat << 'PYTHON'
import requests
import json

API_URL = "http://localhost:5000"

# 1. Crear pedido
print("1. Crear pedido...")
response = requests.post(
    f"{API_URL}/api/pedidos/",
    json={
        "localId": "1",
        "mesaNumero": "Mesa 5",
        "items": [
            {
                "productoId": "1",
                "cantidad": 2,
                "precio": 9500,
                "comentario": "Sin cebolla"
            }
        ],
        "total": 19000
    }
)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
pedido_id = response.json()["id"]

# 2. Obtener detalle del pedido
print("\n2. Obtener detalle del pedido...")
response = requests.get(f"{API_URL}/api/pedidos/{pedido_id}")
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

# 3. Agregar item
print("\n3. Agregar item al pedido...")
response = requests.post(
    f"{API_URL}/api/pedidos/{pedido_id}/items",
    json={
        "productoId": "2",
        "cantidad": 1,
        "observaciones": "Sin picante"
    }
)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
item_id = response.json()["id"]

# 4. Actualizar item
print("\n4. Actualizar item...")
response = requests.put(
    f"{API_URL}/api/pedidos/{pedido_id}/items/{item_id}",
    json={
        "cantidad": 2,
        "observaciones": "Sin sal"
    }
)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

# 5. Obtener mis pedidos (con autenticación)
print("\n5. Obtener mis pedidos...")
headers = {"Authorization": "Bearer tu-token-aqui"}
response = requests.get(
    f"{API_URL}/api/pedidos/mis-pedidos",
    headers=headers
)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

# 6. Eliminar item
print("\n6. Eliminar item...")
response = requests.delete(
    f"{API_URL}/api/pedidos/{pedido_id}/items/{item_id}"
)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
PYTHON

echo -e "\n${BLUE}=================================="
echo "Testing completado"
echo "==================================${NC}"
