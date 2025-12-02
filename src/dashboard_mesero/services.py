"""
Servicios (Lógica de Negocio) para Dashboard Mesero
====================================================

Contiene la lógica de negocio:
- Crear pedidos
- Agregar/actualizar/eliminar items
- Calcular totales
- Validar datos contra BD

Funciones utilizadas por las rutas (routes.py)
"""

from sqlalchemy.orm import Session
from sqlalchemy import select
import logging
from typing import Optional, List, Dict, Tuple

from models.models import (
    Pedido, Cuenta, Producto, Local, Mesa, Usuario,
    EstadoPedidoEnum
)

logger = logging.getLogger(__name__)


def crear_pedido(
    db: Session,
    local_id: int,
    items: List[Dict],
    total: int,
    usuario_id: Optional[int] = None,
    mesa_id: Optional[int] = None
) -> Pedido:
    """
    Crea un nuevo pedido en la BD.
    
    Args:
        db: Sesión de base de datos
        local_id: ID del local
        items: Lista de dicts con {productoId, cantidad, precio, comentario}
        total: Total del pedido (validado por frontend)
        usuario_id: ID del usuario que crea el pedido (opcional)
        mesa_id: ID de la mesa (opcional)
    
    Returns:
        Pedido creado
    
    Raises:
        ValueError: Si el local no existe o hay datos inválidos
    """
    # Validar que el local existe
    local = db.query(Local).filter(Local.id == local_id).first()
    if not local:
        raise ValueError(f"Local con ID {local_id} no encontrado")
    
    # Validar que cada producto existe
    for item in items:
        producto = db.query(Producto).filter(Producto.id == int(item['productoId'])).first()
        if not producto:
            raise ValueError(f"Producto con ID {item['productoId']} no encontrado")
        # Validar que el producto está disponible
        if producto.estado.value != 'disponible':
            raise ValueError(f"Producto {producto.nombre} no está disponible")
    
    # Crear pedido
    pedido = Pedido(
        local_id=local_id,
        mesa_id=mesa_id,
        usuario_id=usuario_id,
        estado=EstadoPedidoEnum.ABIERTO,
        total=total
    )
    
    db.add(pedido)
    db.flush()  # Para obtener el ID del pedido
    
    # Crear items (cuentas) del pedido
    for item in items:
        producto_id = int(item['productoId'])
        cantidad = int(item['cantidad'])
        observaciones = item.get('comentario', '') or ''
        
        cuenta = Cuenta(
            id_pedido=pedido.id,
            id_producto=producto_id,
            cantidad=cantidad,
            observaciones=observaciones
        )
        db.add(cuenta)
    
    db.commit()
    
    logger.info(f"✓ Pedido creado: ID={pedido.id}, local={local_id}, total=${total}")
    
    return pedido


def obtener_pedido(db: Session, pedido_id: int) -> Optional[Pedido]:
    """
    Obtiene un pedido con todos sus items.
    
    Args:
        db: Sesión de base de datos
        pedido_id: ID del pedido
    
    Returns:
        Pedido si existe, None si no
    """
    from sqlalchemy.orm import joinedload
    
    pedido = db.query(Pedido)\
        .options(
            joinedload(Pedido.cuentas).joinedload(Cuenta.producto),
            joinedload(Pedido.local),
            joinedload(Pedido.usuario)
        )\
        .filter(Pedido.id == pedido_id)\
        .first()
    
    return pedido


def obtener_mis_pedidos(db: Session, usuario_id: int) -> List[Pedido]:
    """
    Obtiene todos los pedidos del usuario autenticado.
    
    Args:
        db: Sesión de base de datos
        usuario_id: ID del usuario autenticado
    
    Returns:
        Lista de pedidos del usuario
    """
    pedidos = db.query(Pedido)\
        .filter(Pedido.usuario_id == usuario_id)\
        .order_by(Pedido.creado_el.desc())\
        .all()
    
    return pedidos


def agregar_item_a_pedido(
    db: Session,
    pedido_id: int,
    producto_id: int,
    cantidad: int,
    observaciones: str = ""
) -> Cuenta:
    """
    Agrega un item (producto) a un pedido existente.
    
    Args:
        db: Sesión de base de datos
        pedido_id: ID del pedido
        producto_id: ID del producto
        cantidad: Cantidad a agregar
        observaciones: Notas especiales (alergias, etc.)
    
    Returns:
        Cuenta creada
    
    Raises:
        ValueError: Si pedido o producto no existen
    """
    # Validar pedido
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise ValueError(f"Pedido con ID {pedido_id} no encontrado")
    
    # Validar producto
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        raise ValueError(f"Producto con ID {producto_id} no encontrado")
    
    if producto.estado.value != 'disponible':
        raise ValueError(f"Producto {producto.nombre} no está disponible")
    
    # Crear cuenta
    cuenta = Cuenta(
        id_pedido=pedido_id,
        id_producto=producto_id,
        cantidad=cantidad,
        observaciones=observaciones
    )
    
    db.add(cuenta)
    db.commit()
    
    # Recalcular total
    _recalcular_total_pedido(db, pedido_id)
    
    logger.info(f"✓ Item agregado a pedido {pedido_id}: producto={producto_id}, cantidad={cantidad}")
    
    return cuenta


def actualizar_item(
    db: Session,
    cuenta_id: int,
    cantidad: Optional[int] = None,
    observaciones: Optional[str] = None
) -> Cuenta:
    """
    Actualiza un item (cantidad u observaciones).
    
    Args:
        db: Sesión de base de datos
        cuenta_id: ID de la cuenta/item
        cantidad: Nueva cantidad (opcional)
        observaciones: Nuevas observaciones (opcional)
    
    Returns:
        Cuenta actualizada
    
    Raises:
        ValueError: Si la cuenta no existe
    """
    cuenta = db.query(Cuenta).filter(Cuenta.id == cuenta_id).first()
    if not cuenta:
        raise ValueError(f"Item (cuenta) con ID {cuenta_id} no encontrado")
    
    if cantidad is not None and cantidad > 0:
        cuenta.cantidad = cantidad
    
    if observaciones is not None:
        cuenta.observaciones = observaciones
    
    db.commit()
    
    # Recalcular total del pedido
    _recalcular_total_pedido(db, cuenta.id_pedido)
    
    logger.info(f"✓ Item {cuenta_id} actualizado")
    
    return cuenta


def eliminar_item(db: Session, cuenta_id: int) -> int:
    """
    Elimina un item de un pedido.
    
    Args:
        db: Sesión de base de datos
        cuenta_id: ID de la cuenta/item a eliminar
    
    Returns:
        ID del pedido al que pertenecía (para recalcular total)
    
    Raises:
        ValueError: Si el item no existe
    """
    cuenta = db.query(Cuenta).filter(Cuenta.id == cuenta_id).first()
    if not cuenta:
        raise ValueError(f"Item (cuenta) con ID {cuenta_id} no encontrado")
    
    pedido_id = cuenta.id_pedido
    
    db.delete(cuenta)
    db.commit()
    
    # Recalcular total
    _recalcular_total_pedido(db, pedido_id)
    
    logger.info(f"✓ Item {cuenta_id} eliminado del pedido {pedido_id}")
    
    return pedido_id


def _recalcular_total_pedido(db: Session, pedido_id: int) -> int:
    """
    Recalcula el total del pedido basado en sus items.
    
    NOTA: Esta función se llama automáticamente después de agregar/actualizar/eliminar items.
    
    Args:
        db: Sesión de base de datos
        pedido_id: ID del pedido
    
    Returns:
        Nuevo total del pedido
    """
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        return 0
    
    # Obtener todos los items
    cuentas = db.query(Cuenta)\
        .options(joinedload_from(Cuenta, Cuenta.producto))\
        .filter(Cuenta.id_pedido == pedido_id)\
        .all()
    
    # Calcular total
    nuevo_total = sum(c.producto.precio * c.cantidad for c in cuentas)
    
    # Actualizar pedido
    pedido.total = nuevo_total
    db.commit()
    
    return nuevo_total


def formato_respuesta_pedido(pedido: Pedido) -> Dict:
    """
    Convierte un objeto Pedido a dict formateado para la respuesta API.
    
    Args:
        pedido: Objeto Pedido de la BD
    
    Returns:
        Dict con estructura esperada por el frontend
    """
    items = []
    for cuenta in pedido.cuentas:
        items.append({
            'id': cuenta.id,
            'producto_id': cuenta.id_producto,
            'producto_nombre': cuenta.producto.nombre if cuenta.producto else 'Desconocido',
            'precio_unitario': cuenta.producto.precio if cuenta.producto else 0,
            'cantidad': cuenta.cantidad,
            'subtotal': (cuenta.producto.precio if cuenta.producto else 0) * cuenta.cantidad,
            'observaciones': cuenta.observaciones
        })
    
    return {
        'id': pedido.id,
        'local_id': pedido.local_id,
        'mesa_id': pedido.mesa_id,
        'usuario_id': pedido.usuario_id,
        'estado': pedido.estado.value if pedido.estado else 'abierto',
        'total': pedido.total,
        'items': items,
        'creado_el': pedido.creado_el.isoformat() if pedido.creado_el else None
    }


def formato_respuesta_pedido_creado(pedido: Pedido) -> Dict:
    """
    Convierte un objeto Pedido a dict formateado para respuesta de POST (creación).
    
    Retorna exactamente lo que el frontend espera:
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
    
    Args:
        pedido: Objeto Pedido de la BD
    
    Returns:
        Dict con estructura esperada por frontend
    """
    return {
        'pedidoId': pedido.id,
        'id': pedido.id,
        'localId': str(pedido.local_id),
        'mesaNumero': f"Mesa {pedido.mesa_id}" if pedido.mesa_id else None,
        'estado': pedido.estado.value if pedido.estado else 'abierto',
        'total': pedido.total
    }


# Import lazy para evitar circular imports
def joinedload_from(entity, attr):
    """Helper para joinedload con relaciones"""
    from sqlalchemy.orm import joinedload
    return joinedload(entity, attr)
