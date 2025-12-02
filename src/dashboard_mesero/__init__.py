"""
Dashboard Mesero - Módulo para gestión de pedidos y carrito
=============================================================

Este módulo contiene toda la lógica para:
- Crear y gestionar pedidos
- Agregar/editar/eliminar items del carrito
- Calcular totales
- Validar datos según el frontend esperado

Estructura:
- schemas.py: Validación de datos (Pydantic)
- services.py: Lógica de negocio (crear pedidos, calcular totales, etc.)
- routes.py: Endpoints REST (/api/pedidos/*)

El módulo se integra con:
- models.Pedido, models.Cuenta, models.Producto (tablas existentes)
- utils.jwt_helper (autenticación)
- database.SessionLocal (sesiones de BD)

Endpoints implementados:
- POST   /api/pedidos/               - Crear pedido
- GET    /api/pedidos/{id}           - Obtener detalle del pedido
- GET    /api/pedidos/mis-pedidos    - Obtener mis pedidos (autenticado)
- POST   /api/pedidos/{id}/items     - Agregar item al pedido
- PUT    /api/pedidos/{id}/items/{cuenta_id} - Actualizar item
- DELETE /api/pedidos/{id}/items/{cuenta_id} - Eliminar item
"""

__version__ = "1.0.0"
__author__ = "RestoMap Team"
