"""
Schemas (Pydantic) para validación de datos del Dashboard Mesero
================================================================

Define la estructura exacta que espera el frontend para:
- Crear pedidos
- Items del carrito
- Respuestas de API

Todos los campos incluyen validaciones y tipos según frontend.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


class ItemPedidoCreate(BaseModel):
    """
    Schema para item que se envía al crear/actualizar pedido.
    
    Corresponde exactamente a lo que el frontend envía:
    ```json
    {
      "productoId": "1",
      "cantidad": 2,
      "precio": 9500,
      "comentario": "Sin cebolla"  // opcional
    }
    ```
    """
    productoId: str = Field(..., description="ID del producto")
    cantidad: int = Field(..., gt=0, description="Cantidad (debe ser > 0)")
    precio: int = Field(..., gt=0, description="Precio unitario del producto")
    comentario: Optional[str] = Field(None, description="Notas especiales (alergias, preferencias)")

    @validator('productoId')
    def productoId_no_vacio(cls, v):
        if not v or not v.strip():
            raise ValueError('productoId no puede estar vacío')
        return v.strip()

    @validator('comentario')
    def comentario_longitud(cls, v):
        if v and len(v) > 500:
            raise ValueError('comentario no puede exceder 500 caracteres')
        return v


class PedidoCreate(BaseModel):
    """
    Schema para crear un pedido.
    
    Corresponde exactamente a lo que el frontend envía:
    ```json
    {
      "localId": "1",
      "mesaNumero": "Mesa 5",
      "items": [...],
      "total": 26800
    }
    ```
    """
    localId: str = Field(..., description="ID del local/restaurante")
    mesaNumero: str = Field(..., description="Número/nombre de la mesa (ej: Mesa 5, T1, A-12)")
    items: List[ItemPedidoCreate] = Field(..., min_items=1, description="Al menos 1 item debe haber")
    total: int = Field(..., gt=0, description="Total del pedido (sumatoria de precio * cantidad)")

    @validator('localId')
    def localId_valido(cls, v):
        if not v or not v.strip():
            raise ValueError('localId no puede estar vacío')
        return v.strip()

    @validator('mesaNumero')
    def mesaNumero_valido(cls, v):
        if not v or not v.strip():
            raise ValueError('mesaNumero no puede estar vacío')
        if len(v) > 50:
            raise ValueError('mesaNumero no puede exceder 50 caracteres')
        return v.strip()


class ItemPedidoUpdate(BaseModel):
    """
    Schema para actualizar un item del pedido.
    Todos los campos son opcionales (solo se actualiza lo que se envíe).
    """
    cantidad: Optional[int] = Field(None, gt=0, description="Nueva cantidad")
    observaciones: Optional[str] = Field(None, description="Nuevas observaciones")

    @validator('observaciones')
    def observaciones_longitud(cls, v):
        if v and len(v) > 500:
            raise ValueError('observaciones no puede exceder 500 caracteres')
        return v


class ItemPedidoResponse(BaseModel):
    """
    Schema para respuesta de item en detalle del pedido.
    
    Lo que el backend retorna cuando se consulta un pedido.
    """
    id: int = Field(..., description="ID de la cuenta/item")
    producto_id: int = Field(..., description="ID del producto")
    producto_nombre: str = Field(..., description="Nombre del producto")
    precio_unitario: int = Field(..., description="Precio unitario")
    cantidad: int = Field(..., description="Cantidad pedida")
    subtotal: int = Field(..., description="subtotal = precio_unitario * cantidad")
    observaciones: str = Field(..., description="Notas especiales")

    class Config:
        from_attributes = True


class PedidoDetailResponse(BaseModel):
    """
    Schema para respuesta de detalle del pedido.
    
    Lo que retorna GET /api/pedidos/{id}
    """
    id: int = Field(..., description="ID del pedido")
    local_id: int = Field(..., description="ID del local")
    mesa_id: Optional[int] = Field(None, description="ID de la mesa (si aplica)")
    usuario_id: Optional[int] = Field(None, description="ID del usuario que creó el pedido")
    estado: str = Field(..., description="Estado del pedido (abierto, en_preparacion, servido, cerrado, cancelado)")
    total: int = Field(..., description="Total del pedido")
    items: List[ItemPedidoResponse] = Field(..., description="Items del pedido")
    creado_el: datetime = Field(..., description="Fecha de creación")

    class Config:
        from_attributes = True


class PedidoCreateResponse(BaseModel):
    """
    Schema para respuesta al crear un pedido.
    
    Exactamente lo que el frontend espera recibir (201):
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
    """
    pedidoId: int = Field(..., description="ID del pedido creado (para compatibilidad frontend)")
    id: int = Field(..., description="ID del pedido (alternativa a pedidoId)")
    localId: str = Field(..., description="ID del local")
    mesaNumero: Optional[str] = Field(None, description="Número de mesa (si se guardó)")
    estado: str = Field(..., description="Estado inicial (siempre 'abierto' al crear)")
    total: int = Field(..., description="Total del pedido")

    class Config:
        from_attributes = True


class MisOrdenesResponse(BaseModel):
    """
    Schema para respuesta de GET /api/pedidos/mis-pedidos
    
    Retorna lista de pedidos del usuario autenticado.
    """
    id: int
    localId: int
    estado: str
    total: int
    creado_el: datetime
    items_count: int = Field(..., description="Cantidad de items en el pedido")

    class Config:
        from_attributes = True
