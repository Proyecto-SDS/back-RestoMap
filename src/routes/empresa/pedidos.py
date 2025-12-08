"""
Rutas para gestión de pedidos del local
Prefix: /api/empresa/pedidos/*
"""

import contextlib
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from pydantic import BaseModel, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from database import get_session
from models.models import (
    TIEMPO_EXTENSION_POR_ESTADO,
    Cuenta,
    EstadoPedidoEnum,
    Pedido,
    Producto,
)
from routes.empresa import requerir_empleado, requerir_roles_empresa
from utils.jwt_helper import requerir_auth
from websockets import emit_estado_pedido, emit_expiracion_actualizada

pedidos_bp = Blueprint("pedidos", __name__, url_prefix="/pedidos")


# ============================================
# SCHEMAS
# ============================================


class PedidoEstadoSchema(BaseModel):
    estado: EstadoPedidoEnum
    nota: str | None = None


# ============================================
# ENDPOINTS
# ============================================


@pedidos_bp.route("/", methods=["GET"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente", "mesero", "cocinero", "bartender")
def listar_pedidos(user_id, user_rol, id_local):
    """Listar todos los pedidos del local"""
    estado_filter = request.args.get("estado")
    mesa_id_filter = request.args.get("mesa_id")

    db = get_session()
    try:
        stmt = (
            select(Pedido)
            .options(
                joinedload(Pedido.mesa),
                joinedload(Pedido.cuentas).joinedload(Cuenta.producto),
            )
            .where(Pedido.id_local == id_local)
            .order_by(Pedido.creado_el.desc())
        )

        if estado_filter:
            try:
                estado_enum = EstadoPedidoEnum(estado_filter)
                stmt = stmt.where(Pedido.estado == estado_enum)
            except ValueError:
                pass

        if mesa_id_filter:
            stmt = stmt.where(Pedido.id_mesa == int(mesa_id_filter))

        pedidos = db.execute(stmt).unique().scalars().all()

        result = []
        for pedido in pedidos:
            lineas = []
            for cuenta in pedido.cuentas:
                lineas.append(
                    {
                        "id": cuenta.id,
                        "producto_id": cuenta.id_producto,
                        "producto_nombre": cuenta.producto.nombre
                        if cuenta.producto
                        else "Producto eliminado",
                        "cantidad": cuenta.cantidad,
                        "precio_unitario": cuenta.producto.precio
                        if cuenta.producto
                        else 0,
                        "observaciones": cuenta.observaciones,
                    }
                )

            result.append(
                {
                    "id": pedido.id,
                    "id_mesa": pedido.id_mesa,
                    "mesa_nombre": pedido.mesa.nombre if pedido.mesa else None,
                    "estado": pedido.estado.value if pedido.estado else None,
                    "total": pedido.total,
                    "creado_el": pedido.creado_el.isoformat()
                    if pedido.creado_el
                    else None,
                    "lineas": lineas,
                }
            )

        return jsonify(result), 200
    finally:
        db.close()


@pedidos_bp.route("/<int:pedido_id>", methods=["GET"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente", "mesero", "cocinero", "bartender")
def obtener_pedido(pedido_id, user_id, user_rol, id_local):
    """Obtener detalle de un pedido específico"""
    db = get_session()
    try:
        stmt = (
            select(Pedido)
            .options(
                joinedload(Pedido.mesa),
                joinedload(Pedido.cuentas).joinedload(Cuenta.producto),
            )
            .where(Pedido.id == pedido_id, Pedido.id_local == id_local)
        )
        pedido = db.execute(stmt).unique().scalar_one_or_none()

        if not pedido:
            return jsonify({"error": "Pedido no encontrado"}), 404

        lineas = []
        for cuenta in pedido.cuentas:
            lineas.append(
                {
                    "id": cuenta.id,
                    "producto_id": cuenta.id_producto,
                    "producto_nombre": cuenta.producto.nombre
                    if cuenta.producto
                    else "Producto eliminado",
                    "cantidad": cuenta.cantidad,
                    "precio_unitario": cuenta.producto.precio if cuenta.producto else 0,
                    "observaciones": cuenta.observaciones,
                }
            )

        return jsonify(
            {
                "id": pedido.id,
                "id_mesa": pedido.id_mesa,
                "mesa_nombre": pedido.mesa.nombre if pedido.mesa else None,
                "estado": pedido.estado.value if pedido.estado else None,
                "total": pedido.total,
                "creado_el": pedido.creado_el.isoformat() if pedido.creado_el else None,
                "lineas": lineas,
            }
        ), 200
    finally:
        db.close()


@pedidos_bp.route("/<int:pedido_id>/estado", methods=["PATCH"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente", "mesero", "cocinero", "bartender")
def cambiar_estado_pedido(pedido_id, user_id, user_rol, id_local):
    """Cambiar estado de un pedido"""
    try:
        data = PedidoEstadoSchema(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": "Datos inválidos", "details": e.errors()}), 400

    db = get_session()
    try:
        stmt = (
            select(Pedido)
            .options(joinedload(Pedido.qr))
            .where(Pedido.id == pedido_id, Pedido.id_local == id_local)
        )
        pedido = db.execute(stmt).scalar_one_or_none()

        if not pedido:
            return jsonify({"error": "Pedido no encontrado"}), 404

        if not EstadoPedidoEnum.flujo_valido(pedido.estado, data.estado):
            return jsonify(
                {
                    "error": "Transición de estado no permitida",
                    "estado_actual": pedido.estado.value if pedido.estado else None,
                    "estado_nuevo": data.estado.value,
                }
            ), 400

        pedido.estado = data.estado

        # Extender expiración si cambia a EN_PROCESO
        if data.estado == EstadoPedidoEnum.EN_PROCESO:
            pedido.expiracion = (pedido.expiracion or datetime.now()) + timedelta(
                minutes=TIEMPO_EXTENSION_POR_ESTADO[EstadoPedidoEnum.EN_PROCESO]
            )

        # Desactivar QR si el pedido terminó (completado o cancelado)
        if (
            data.estado in [EstadoPedidoEnum.COMPLETADO, EstadoPedidoEnum.CANCELADO]
            and pedido.qr
        ):
            pedido.qr.activo = False

        db.commit()

        # Emitir evento WebSocket - Estado del pedido actualizado
        with contextlib.suppress(Exception):
            emit_estado_pedido(id_local, pedido.id, data.estado.value)
            # Si cambió la expiración, notificar para actualizar timer
            if data.estado == EstadoPedidoEnum.EN_PROCESO and pedido.id_mesa:
                emit_expiracion_actualizada(
                    id_local,
                    pedido.id_mesa,
                    pedido.expiracion.isoformat() if pedido.expiracion else None,
                )

        return jsonify(
            {
                "message": "Estado del pedido actualizado",
                "pedido": {"id": pedido.id, "estado": pedido.estado.value},
            }
        ), 200
    finally:
        db.close()


@pedidos_bp.route("/<int:pedido_id>/extender", methods=["POST"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente", "mesero")
def extender_tiempo_pedido(pedido_id, user_id, user_rol, id_local):
    """
    Extender tiempo de expiración del pedido.

    Body (opcional):
        { "minutos": 5 }  # Default: 5, máximo: 30
    """
    db = get_session()
    try:
        # Obtener minutos del body (default 5, máximo 30)
        data = request.get_json() or {}
        minutos = min(data.get("minutos", 5), 30)

        stmt = select(Pedido).where(Pedido.id == pedido_id, Pedido.id_local == id_local)
        pedido = db.execute(stmt).scalar_one_or_none()

        if not pedido:
            return jsonify({"error": "Pedido no encontrado"}), 404

        # Permitir extender en cualquier estado activo
        if pedido.estado in [EstadoPedidoEnum.COMPLETADO, EstadoPedidoEnum.CANCELADO]:
            return jsonify(
                {
                    "error": "No se puede extender tiempo de pedido finalizado",
                    "estado_actual": pedido.estado.value if pedido.estado else None,
                }
            ), 400

        # Extender tiempo
        pedido.expiracion = (pedido.expiracion or datetime.now()) + timedelta(
            minutes=minutos
        )
        db.commit()

        # Emitir evento para actualizar timer en frontend
        if pedido.id_mesa:
            with contextlib.suppress(Exception):
                emit_expiracion_actualizada(
                    id_local,
                    pedido.id_mesa,
                    pedido.expiracion.isoformat() if pedido.expiracion else None,
                )

        return jsonify(
            {
                "message": f"Tiempo extendido +{minutos} minutos",
                "pedido": {
                    "id": pedido.id,
                    "expiracion": pedido.expiracion.isoformat()
                    if pedido.expiracion
                    else None,
                },
            }
        ), 200
    finally:
        db.close()


@pedidos_bp.route("/cocina", methods=["GET"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente", "cocinero")
def pedidos_cocina(user_id, user_rol, id_local):
    """Listar pedidos para la cocina - Solo productos tipo Comida"""
    estados_cocina = [
        EstadoPedidoEnum.RECEPCION,
        EstadoPedidoEnum.EN_PROCESO,
        EstadoPedidoEnum.TERMINADO,
    ]

    db = get_session()
    try:
        stmt = (
            select(Pedido)
            .options(
                joinedload(Pedido.mesa),
                joinedload(Pedido.cuentas)
                .joinedload(Cuenta.producto)
                .joinedload(Producto.categoria),
            )
            .where(Pedido.id_local == id_local, Pedido.estado.in_(estados_cocina))
            .order_by(Pedido.creado_el.asc())
        )

        pedidos = db.execute(stmt).unique().scalars().all()

        result = []
        for pedido in pedidos:
            lineas = []
            for cuenta in pedido.cuentas:
                # Solo incluir productos tipo Comida (id_tipo_categoria=1)
                if (
                    cuenta.producto
                    and cuenta.producto.categoria
                    and cuenta.producto.categoria.id_tipo_categoria == 1
                ):
                    lineas.append(
                        {
                            "id": cuenta.id,
                            "producto_id": cuenta.id_producto,
                            "producto_nombre": cuenta.producto.nombre,
                            "cantidad": cuenta.cantidad,
                            "observaciones": cuenta.observaciones,
                        }
                    )

            # Solo agregar pedido si tiene lineas de comida
            if lineas:
                result.append(
                    {
                        "id": pedido.id,
                        "id_mesa": pedido.id_mesa,
                        "mesa_nombre": pedido.mesa.nombre if pedido.mesa else None,
                        "estado": pedido.estado.value if pedido.estado else None,
                        "creado_el": pedido.creado_el.isoformat()
                        if pedido.creado_el
                        else None,
                        "actualizado_el": pedido.actualizado_el.isoformat()
                        if pedido.actualizado_el
                        else None,
                        "lineas": lineas,
                    }
                )

        return jsonify(result), 200
    finally:
        db.close()


@pedidos_bp.route("/barra", methods=["GET"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente", "bartender")
def pedidos_barra(user_id, user_rol, id_local):
    """Listar pedidos para la barra - Solo productos tipo Bebida"""
    estados_barra = [
        EstadoPedidoEnum.RECEPCION,
        EstadoPedidoEnum.EN_PROCESO,
        EstadoPedidoEnum.TERMINADO,
    ]

    db = get_session()
    try:
        stmt = (
            select(Pedido)
            .options(
                joinedload(Pedido.mesa),
                joinedload(Pedido.cuentas)
                .joinedload(Cuenta.producto)
                .joinedload(Producto.categoria),
            )
            .where(Pedido.id_local == id_local, Pedido.estado.in_(estados_barra))
            .order_by(Pedido.creado_el.asc())
        )

        pedidos = db.execute(stmt).unique().scalars().all()

        result = []
        for pedido in pedidos:
            lineas = []
            for cuenta in pedido.cuentas:
                # Solo incluir productos tipo Bebida (id_tipo_categoria=2)
                if (
                    cuenta.producto
                    and cuenta.producto.categoria
                    and cuenta.producto.categoria.id_tipo_categoria == 2
                ):
                    lineas.append(
                        {
                            "id": cuenta.id,
                            "producto_id": cuenta.id_producto,
                            "producto_nombre": cuenta.producto.nombre,
                            "cantidad": cuenta.cantidad,
                            "observaciones": cuenta.observaciones,
                        }
                    )

            # Solo agregar pedido si tiene lineas de bebida
            if lineas:
                result.append(
                    {
                        "id": pedido.id,
                        "id_mesa": pedido.id_mesa,
                        "mesa_nombre": pedido.mesa.nombre if pedido.mesa else None,
                        "estado": pedido.estado.value if pedido.estado else None,
                        "creado_el": pedido.creado_el.isoformat()
                        if pedido.creado_el
                        else None,
                        "actualizado_el": pedido.actualizado_el.isoformat()
                        if pedido.actualizado_el
                        else None,
                        "lineas": lineas,
                    }
                )

        return jsonify(result), 200
    finally:
        db.close()
