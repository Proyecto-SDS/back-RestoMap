"""
Rutas para gestión de pedidos del local
Prefix: /api/empresa/pedidos/*
"""

import contextlib

from flask import Blueprint, jsonify, request
from pydantic import BaseModel, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from database import get_session
from models.models import Cuenta, EstadoPedidoEnum, Pedido
from routes.empresa import requerir_empleado, requerir_roles_empresa
from utils.jwt_helper import requerir_auth
from websockets import emit_estado_pedido

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

        return jsonify(
            {
                "message": "Estado del pedido actualizado",
                "pedido": {"id": pedido.id, "estado": pedido.estado.value},
            }
        ), 200
    finally:
        db.close()


@pedidos_bp.route("/cocina", methods=["GET"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente", "cocinero")
def pedidos_cocina(user_id, user_rol, id_local):
    """Listar pedidos para la cocina"""
    estados_cocina = [
        EstadoPedidoEnum.INICIADO,
        EstadoPedidoEnum.RECEPCION,
        EstadoPedidoEnum.EN_PROCESO,
    ]

    db = get_session()
    try:
        stmt = (
            select(Pedido)
            .options(
                joinedload(Pedido.mesa),
                joinedload(Pedido.cuentas).joinedload(Cuenta.producto),
            )
            .where(Pedido.id_local == id_local, Pedido.estado.in_(estados_cocina))
            .order_by(Pedido.creado_el.asc())
        )

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
                        "observaciones": cuenta.observaciones,
                    }
                )

            result.append(
                {
                    "id": pedido.id,
                    "id_mesa": pedido.id_mesa,
                    "mesa_nombre": pedido.mesa.nombre if pedido.mesa else None,
                    "estado": pedido.estado.value if pedido.estado else None,
                    "creado_el": pedido.creado_el.isoformat()
                    if pedido.creado_el
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
    """Listar pedidos para la barra"""
    estados_barra = [
        EstadoPedidoEnum.INICIADO,
        EstadoPedidoEnum.RECEPCION,
        EstadoPedidoEnum.EN_PROCESO,
    ]

    db = get_session()
    try:
        stmt = (
            select(Pedido)
            .options(
                joinedload(Pedido.mesa),
                joinedload(Pedido.cuentas).joinedload(Cuenta.producto),
            )
            .where(Pedido.id_local == id_local, Pedido.estado.in_(estados_barra))
            .order_by(Pedido.creado_el.asc())
        )

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
                        "observaciones": cuenta.observaciones,
                    }
                )

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
                        "lineas": lineas,
                    }
                )

        return jsonify(result), 200
    finally:
        db.close()
