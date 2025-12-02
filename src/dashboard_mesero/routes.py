"""
Rutas (Endpoints) del Dashboard Mesero
=======================================

Implementa todos los endpoints REST para gestión de pedidos:
- POST   /api/pedidos/               - Crear pedido
- GET    /api/pedidos/{id}           - Obtener detalle del pedido
- GET    /api/pedidos/mis-pedidos    - Obtener mis pedidos (requiere auth)
- POST   /api/pedidos/{id}/items     - Agregar item al pedido
- PUT    /api/pedidos/{id}/items/{cuenta_id} - Actualizar item
- DELETE /api/pedidos/{id}/items/{cuenta_id} - Eliminar item

Todos los endpoints retornan JSON según especificación del frontend.
"""

from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
import logging
from typing import Optional
from pydantic import ValidationError

from database import SessionLocal
from utils.jwt_helper import requerir_auth
from models.models import Pedido, Cuenta, Producto

from . import services, schemas

logger = logging.getLogger(__name__)

# Crear Blueprint para rutas de pedidos
pedidos_bp = Blueprint('pedidos', __name__, url_prefix='/api/pedidos')


def get_db():
    """Obtener sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# POST /api/pedidos/
# ============================================================================

@pedidos_bp.route('/', methods=['POST'])
def crear_pedido():
    """
    Crear un nuevo pedido.
    
    **Request body (exactamente como envía el frontend):**
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
        }
      ],
      "total": 26800
    }
    ```
    
    **Response 201 (exactamente como espera el frontend):**
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
    
    **Response 400:**
    - Datos inválidos o incompletos
    
    **Response 500:**
    - Error al crear el pedido (producto no existe, local no existe, etc.)
    """
    try:
        data = request.get_json()
        
        # Validar datos con Pydantic
        pedido_data = schemas.PedidoCreate(**data)
        
        db = next(get_db())
        
        # Crear pedido en BD
        pedido = services.crear_pedido(
            db=db,
            local_id=int(pedido_data.localId),
            items=[
                {
                    'productoId': item.productoId,
                    'cantidad': item.cantidad,
                    'precio': item.precio,
                    'comentario': item.comentario
                }
                for item in pedido_data.items
            ],
            total=pedido_data.total
        )
        
        # Retornar exactamente lo que espera el frontend
        respuesta = services.formato_respuesta_pedido_creado(pedido)
        
        logger.info(f"✓ Pedido creado exitosamente: {respuesta}")
        
        return jsonify(respuesta), 201
    
    except ValidationError as e:
        logger.warning(f"✗ Validación fallida: {e}")
        return jsonify({'error': 'Datos inválidos', 'detalles': str(e)}), 400
    
    except ValueError as e:
        logger.warning(f"✗ Error de negocio: {e}")
        return jsonify({'error': str(e)}), 400
    
    except Exception as e:
        logger.error(f"✗ Error al crear pedido: {e}")
        return jsonify({'error': 'Error al crear el pedido'}), 500


# ============================================================================
# GET /api/pedidos/{id}
# ============================================================================

@pedidos_bp.route('/<int:pedido_id>', methods=['GET'])
def obtener_pedido(pedido_id: int):
    """
    Obtener detalle completo de un pedido.
    
    **Response 200:**
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
        }
      ],
      "creado_el": "2025-12-01T10:30:00"
    }
    ```
    
    **Response 404:**
    - Pedido no encontrado
    """
    try:
        db = next(get_db())
        
        pedido = services.obtener_pedido(db, pedido_id)
        
        if not pedido:
            return jsonify({'error': f'Pedido con ID {pedido_id} no encontrado'}), 404
        
        respuesta = services.formato_respuesta_pedido(pedido)
        
        return jsonify(respuesta), 200
    
    except Exception as e:
        logger.error(f"✗ Error al obtener pedido {pedido_id}: {e}")
        return jsonify({'error': 'Error al obtener el pedido'}), 500


# ============================================================================
# GET /api/pedidos/mis-pedidos
# ============================================================================

@pedidos_bp.route('/mis-pedidos', methods=['GET'])
@requerir_auth
def obtener_mis_pedidos(user_id: int, user_rol: str):
    """
    Obtener todos los pedidos del usuario autenticado.
    
    **Headers requeridos:**
    - Authorization: Bearer {token}
    
    **Response 200:**
    ```json
    [
      {
        "id": 1,
        "localId": 1,
        "estado": "abierto",
        "total": 26800,
        "creado_el": "2025-12-01T10:30:00",
        "items_count": 3
      },
      {
        "id": 2,
        "localId": 2,
        "estado": "cerrado",
        "total": 15500,
        "creado_el": "2025-11-30T19:45:00",
        "items_count": 2
      }
    ]
    ```
    
    **Response 401:**
    - No autenticado o token inválido
    """
    try:
        db = next(get_db())
        
        pedidos = services.obtener_mis_pedidos(db, user_id)
        
        respuesta = [
            {
                'id': p.id,
                'localId': p.local_id,
                'estado': p.estado.value if p.estado else 'abierto',
                'total': p.total,
                'creado_el': p.creado_el.isoformat() if p.creado_el else None,
                'items_count': len(p.cuentas) if p.cuentas else 0
            }
            for p in pedidos
        ]
        
        return jsonify(respuesta), 200
    
    except Exception as e:
        logger.error(f"✗ Error al obtener mis pedidos (usuario {user_id}): {e}")
        return jsonify({'error': 'Error al obtener tus pedidos'}), 500


# ============================================================================
# POST /api/pedidos/{id}/items
# ============================================================================

@pedidos_bp.route('/<int:pedido_id>/items', methods=['POST'])
def agregar_item(pedido_id: int):
    """
    Agregar un item (producto) a un pedido existente.
    
    **Request body:**
    ```json
    {
      "productoId": "2",
      "cantidad": 1,
      "observaciones": "Sin picante"
    }
    ```
    
    **Response 201:**
    ```json
    {
      "id": 2,
      "producto_id": 2,
      "producto_nombre": "Salmón Grillado",
      "precio_unitario": 24000,
      "cantidad": 1,
      "subtotal": 24000,
      "observaciones": "Sin picante"
    }
    ```
    
    **Response 400:**
    - Datos inválidos
    - Producto no disponible
    
    **Response 404:**
    - Pedido no encontrado
    """
    try:
        data = request.get_json()
        
        producto_id = data.get('productoId')
        cantidad = data.get('cantidad', 1)
        observaciones = data.get('observaciones', '')
        
        if not producto_id or cantidad < 1:
            return jsonify({'error': 'productoId y cantidad válida son requeridos'}), 400
        
        db = next(get_db())
        
        # Agregar item
        cuenta = services.agregar_item_a_pedido(
            db=db,
            pedido_id=pedido_id,
            producto_id=int(producto_id),
            cantidad=int(cantidad),
            observaciones=observaciones
        )
        
        respuesta = {
            'id': cuenta.id,
            'producto_id': cuenta.id_producto,
            'producto_nombre': cuenta.producto.nombre,
            'precio_unitario': cuenta.producto.precio,
            'cantidad': cuenta.cantidad,
            'subtotal': cuenta.producto.precio * cuenta.cantidad,
            'observaciones': cuenta.observaciones
        }
        
        return jsonify(respuesta), 201
    
    except ValueError as e:
        logger.warning(f"✗ Error al agregar item a pedido {pedido_id}: {e}")
        return jsonify({'error': str(e)}), 400
    
    except Exception as e:
        logger.error(f"✗ Error al agregar item: {e}")
        return jsonify({'error': 'Error al agregar el item'}), 500


# ============================================================================
# PUT /api/pedidos/{id}/items/{cuenta_id}
# ============================================================================

@pedidos_bp.route('/<int:pedido_id>/items/<int:cuenta_id>', methods=['PUT'])
def actualizar_item(pedido_id: int, cuenta_id: int):
    """
    Actualizar cantidad u observaciones de un item.
    
    **Request body (campos opcionales):**
    ```json
    {
      "cantidad": 2,
      "observaciones": "Sin cebolla, extra picante"
    }
    ```
    
    **Response 200:**
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
    
    **Response 400:**
    - Datos inválidos
    
    **Response 404:**
    - Item no encontrado
    """
    try:
        data = request.get_json()
        
        db = next(get_db())
        
        # Validar que el item existe
        cuenta = db.query(Cuenta).filter(Cuenta.id == cuenta_id).first()
        if not cuenta:
            return jsonify({'error': f'Item con ID {cuenta_id} no encontrado'}), 404
        
        # Actualizar item
        cantidad = data.get('cantidad')
        observaciones = data.get('observaciones')
        
        cuenta = services.actualizar_item(
            db=db,
            cuenta_id=cuenta_id,
            cantidad=cantidad,
            observaciones=observaciones
        )
        
        respuesta = {
            'id': cuenta.id,
            'producto_id': cuenta.id_producto,
            'producto_nombre': cuenta.producto.nombre,
            'precio_unitario': cuenta.producto.precio,
            'cantidad': cuenta.cantidad,
            'subtotal': cuenta.producto.precio * cuenta.cantidad,
            'observaciones': cuenta.observaciones
        }
        
        return jsonify(respuesta), 200
    
    except ValueError as e:
        logger.warning(f"✗ Error al actualizar item {cuenta_id}: {e}")
        return jsonify({'error': str(e)}), 404
    
    except Exception as e:
        logger.error(f"✗ Error al actualizar item: {e}")
        return jsonify({'error': 'Error al actualizar el item'}), 500


# ============================================================================
# DELETE /api/pedidos/{id}/items/{cuenta_id}
# ============================================================================

@pedidos_bp.route('/<int:pedido_id>/items/<int:cuenta_id>', methods=['DELETE'])
def eliminar_item(pedido_id: int, cuenta_id: int):
    """
    Eliminar un item de un pedido.
    
    **Response 200:**
    ```json
    {
      "mensaje": "Item eliminado exitosamente",
      "nuevo_total": 15600
    }
    ```
    
    **Response 404:**
    - Item no encontrado
    """
    try:
        db = next(get_db())
        
        # Eliminar item
        pedido_eliminado = services.eliminar_item(db, cuenta_id)
        
        # Obtener nuevo total
        pedido = services.obtener_pedido(db, pedido_eliminado)
        nuevo_total = pedido.total if pedido else 0
        
        respuesta = {
            'mensaje': 'Item eliminado exitosamente',
            'nuevo_total': nuevo_total
        }
        
        return jsonify(respuesta), 200
    
    except ValueError as e:
        logger.warning(f"✗ Error al eliminar item {cuenta_id}: {e}")
        return jsonify({'error': str(e)}), 404
    
    except Exception as e:
        logger.error(f"✗ Error al eliminar item: {e}")
        return jsonify({'error': 'Error al eliminar el item'}), 500
