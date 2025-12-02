# Dashboard Mesero - Documentación

## Descripción

Módulo que implementa la lógica para gestionar pedidos del dashboard mesero. Permite:

- ✅ Crear nuevos pedidos
- ✅ Obtener detalle de pedidos
- ✅ Agregar items (productos) a pedidos
- ✅ Actualizar cantidad y observaciones de items
- ✅ Eliminar items
- ✅ Calcular totales automáticamente
- ✅ Obtener historial de pedidos del usuario

## Estructura del Módulo

```
src/dashboard_mesero/
├── __init__.py          # Información del módulo
├── schemas.py           # Validación de datos (Pydantic)
├── services.py          # Lógica de negocio
├── routes.py            # Endpoints REST
└── README.md            # Esta documentación
```

## Archivos

### `schemas.py`
Define la validación de datos usando Pydantic:

- `ItemPedidoCreate`: Valida estructura de items al crear pedido
- `PedidoCreate`: Valida estructura completa del pedido
- `ItemPedidoUpdate`: Valida actualizaciones de items
- `PedidoDetailResponse`: Formato de respuesta para detalle
- `PedidoCreateResponse`: Formato de respuesta al crear

**Todos los schemas están diseñados exactamente según lo que espera el frontend.**

### `services.py`
Contiene la lógica de negocio:

- `crear_pedido()`: Crea pedido con sus items
- `obtener_pedido()`: Obtiene detalle completo
- `obtener_mis_pedidos()`: Obtiene pedidos del usuario
- `agregar_item_a_pedido()`: Agrega producto a pedido
- `actualizar_item()`: Actualiza cantidad/observaciones
- `eliminar_item()`: Elimina item del pedido
- `_recalcular_total_pedido()`: Recalcula total automáticamente
- `formato_respuesta_pedido()`: Formatea respuesta para detalle
- `formato_respuesta_pedido_creado()`: Formatea respuesta al crear

### `routes.py`
Implementa todos los endpoints REST:

1. `POST /api/pedidos/` - Crear pedido
2. `GET /api/pedidos/{id}` - Obtener detalle
3. `GET /api/pedidos/mis-pedidos` - Mis pedidos (requiere auth)
4. `POST /api/pedidos/{id}/items` - Agregar item
5. `PUT /api/pedidos/{id}/items/{cuenta_id}` - Actualizar item
6. `DELETE /api/pedidos/{id}/items/{cuenta_id}` - Eliminar item

## Endpoints

### 1. POST `/api/pedidos/`

**Crear un nuevo pedido**

**Request:**
```json
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
```

**Response (201):**
```json
{
  "pedidoId": 1,
  "id": 1,
  "localId": "1",
  "mesaNumero": "Mesa 5",
  "estado": "abierto",
  "total": 26800
}
```

**Códigos HTTP:**
- `201`: Pedido creado exitosamente
- `400`: Datos inválidos o producto no disponible
- `500`: Error del servidor

---

### 2. GET `/api/pedidos/{id}`

**Obtener detalle completo de un pedido**

**Request:**
```
GET /api/pedidos/1
```

**Response (200):**
```json
{
  "id": 1,
  "local_id": 1,
  "mesa_id": 3,
  "usuario_id": 2,
  "estado": "abierto",
  "total": 26800,
  "items": [
    {
      "id": 1,
      "producto_id": 1,
      "producto_nombre": "Lomo a lo Pobre",
      "precio_unitario": 9500,
      "cantidad": 2,
      "subtotal": 19000,
      "observaciones": "Sin cebolla"
    },
    {
      "id": 2,
      "producto_id": 3,
      "producto_nombre": "Pastel de Choclo",
      "precio_unitario": 7800,
      "cantidad": 1,
      "subtotal": 7800,
      "observaciones": ""
    }
  ],
  "creado_el": "2025-12-01T10:30:00"
}
```

**Códigos HTTP:**
- `200`: OK
- `404`: Pedido no encontrado
- `500`: Error del servidor

---

### 3. GET `/api/pedidos/mis-pedidos`

**Obtener todos los pedidos del usuario autenticado**

**Headers requeridos:**
```
Authorization: Bearer {token}
```

**Request:**
```
GET /api/pedidos/mis-pedidos
```

**Response (200):**
```json
[
  {
    "id": 1,
    "localId": 1,
    "estado": "abierto",
    "total": 26800,
    "creado_el": "2025-12-01T10:30:00",
    "items_count": 2
  },
  {
    "id": 2,
    "localId": 2,
    "estado": "cerrado",
    "total": 15500,
    "creado_el": "2025-11-30T19:45:00",
    "items_count": 1
  }
]
```

**Códigos HTTP:**
- `200`: OK
- `401`: No autenticado
- `500`: Error del servidor

---

### 4. POST `/api/pedidos/{id}/items`

**Agregar un producto al pedido**

**Request:**
```json
{
  "productoId": "2",
  "cantidad": 1,
  "observaciones": "Sin picante"
}
```

**Response (201):**
```json
{
  "id": 3,
  "producto_id": 2,
  "producto_nombre": "Salmón Grillado",
  "precio_unitario": 24000,
  "cantidad": 1,
  "subtotal": 24000,
  "observaciones": "Sin picante"
}
```

**Notas:**
- El total del pedido se recalcula automáticamente
- El campo `observaciones` es opcional

**Códigos HTTP:**
- `201`: Item agregado
- `400`: Datos inválidos
- `404`: Pedido o producto no encontrado
- `500`: Error del servidor

---

### 5. PUT `/api/pedidos/{id}/items/{cuenta_id}`

**Actualizar cantidad u observaciones de un item**

**Request:**
```json
{
  "cantidad": 2,
  "observaciones": "Sin cebolla, extra picante"
}
```

**Response (200):**
```json
{
  "id": 1,
  "producto_id": 1,
  "producto_nombre": "Lomo a lo Pobre",
  "precio_unitario": 9500,
  "cantidad": 2,
  "subtotal": 19000,
  "observaciones": "Sin cebolla, extra picante"
}
```

**Notas:**
- Ambos campos (cantidad, observaciones) son opcionales
- El total del pedido se recalcula automáticamente

**Códigos HTTP:**
- `200`: Item actualizado
- `404`: Item no encontrado
- `500`: Error del servidor

---

### 6. DELETE `/api/pedidos/{id}/items/{cuenta_id}`

**Eliminar un item del pedido**

**Request:**
```
DELETE /api/pedidos/1/items/2
```

**Response (200):**
```json
{
  "mensaje": "Item eliminado exitosamente",
  "nuevo_total": 19000
}
```

**Notas:**
- El total del pedido se recalcula automáticamente

**Códigos HTTP:**
- `200`: Item eliminado
- `404`: Item no encontrado
- `500`: Error del servidor

---

## Integración con el Resto del Backend

### Modelos utilizados
- `models.Pedido` - Tabla de pedidos
- `models.Cuenta` - Items del pedido
- `models.Producto` - Productos disponibles
- `models.Local` - Restaurantes
- `models.EstadoPedidoEnum` - Estados (abierto, en_preparacion, servido, cerrado, cancelado)

### Autenticación
- Usa `@requerir_auth` decorator del módulo `utils.jwt_helper`
- El endpoint `GET /api/pedidos/mis-pedidos` requiere token válido

### Base de datos
- Usa `database.SessionLocal` para conexiones
- Todas las operaciones son transaccionales (con db.commit)

---

## Ejemplos de Uso

### Crear un pedido (con curl)

```bash
curl -X POST http://localhost:5000/api/pedidos/ \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

### Obtener detalle del pedido

```bash
curl http://localhost:5000/api/pedidos/1
```

### Agregar item al pedido

```bash
curl -X POST http://localhost:5000/api/pedidos/1/items \
  -H "Content-Type: application/json" \
  -d '{
    "productoId": "2",
    "cantidad": 1,
    "observaciones": "Sin picante"
  }'
```

### Actualizar item

```bash
curl -X PUT http://localhost:5000/api/pedidos/1/items/1 \
  -H "Content-Type: application/json" \
  -d '{
    "cantidad": 3,
    "observaciones": "Sin sal"
  }'
```

### Eliminar item

```bash
curl -X DELETE http://localhost:5000/api/pedidos/1/items/1
```

### Obtener mis pedidos (con autenticación)

```bash
curl http://localhost:5000/api/pedidos/mis-pedidos \
  -H "Authorization: Bearer {token}"
```

---

## Logging

Todos los endpoints registran las operaciones en logs:

```
✓ Pedido creado exitosamente: {"pedidoId": 1, ...}
✓ Item agregado a pedido 1: producto=2, cantidad=1
✓ Item 1 actualizado
✓ Item 1 eliminado del pedido 1
```

Los errores también se registran:

```
✗ Validación fallida: ...
✗ Error de negocio: Producto con ID 999 no encontrado
✗ Error al crear pedido: ...
```

---

## Notas Importantes

1. **Total del pedido se recalcula automáticamente** después de agregar/actualizar/eliminar items
2. **Las observaciones son de texto libre** - puede contener alergias, preferencias, etc.
3. **El campo comentario en la creación es opcional** - puede no venir o ser undefined
4. **La validación de datos es estricta** - usa Pydantic para garantizar integridad
5. **Los productos deben estar "disponibles"** - no se pueden agregar productos agotados o inactivos
6. **No hay persistencia de división de cuenta aún** - se implementará cuando el frontend esté listo

---

## Testing

### Archivos de Testing Disponibles

En la raíz del proyecto hay varios archivos para testing:

1. **`EJEMPLOS_CURL.md`** 
   - Ejemplos listos para copiar/pegar
   - Casos de uso comunes
   - Comandos para debugging

2. **`test_pedidos.ps1`** (Windows PowerShell)
   ```powershell
   # Ejecutar en PowerShell
   .\test_pedidos.ps1
   ```
   - Flujo completo de testing (crear → agregar → actualizar → eliminar)
   - Colores y salida formateada
   - Captura de IDs para usar en siguientes requests

3. **`test_pedidos.sh`** (Bash/Linux/Mac)
   ```bash
   bash test_pedidos.sh
   ```
   - Incluye ejemplos en curl y Python
   - Flujo completo de testing
   - Código comentado para aprender

### Testing Manual

Para probar manualmente, usar:
- **Postman**: Importar endpoints con ejemplos JSON
- **curl**: Usar ejemplos de `EJEMPLOS_CURL.md`
- **Python requests**: Script en `test_pedidos.sh`
- **PowerShell**: Script `test_pedidos.ps1` (recomendado en Windows)

---

## Cambios Futuros

- [ ] Implementar endpoint de QR dinámico: `POST /api/qr/generar`
- [ ] Agregar soporte para división de cuenta por item
- [ ] Implementar historial de cambios de estado
- [ ] Agregar validaciones de horarios
- [ ] Implementar límites de cantidad por producto
