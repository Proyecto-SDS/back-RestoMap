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
    EstadoPagoEnum,
    EstadoPedidoEnum,
    MetodoPagoEnum,
    Pago,
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


class RegistrarPagoSchema(BaseModel):
    metodo: MetodoPagoEnum
    monto: int


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
            .options(joinedload(Pedido.qr), joinedload(Pedido.mesa))
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

        # Liberar mesa si el pedido se completó o canceló
        if data.estado in [EstadoPedidoEnum.COMPLETADO, EstadoPedidoEnum.CANCELADO]:
            if pedido.mesa:
                from models.models import EstadoMesaEnum

                pedido.mesa.estado = EstadoMesaEnum.DISPONIBLE

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
            # Si se liberó la mesa, notificar actualización de estado de mesa
            if (
                data.estado in [EstadoPedidoEnum.COMPLETADO, EstadoPedidoEnum.CANCELADO]
                and pedido.id_mesa
            ):
                from websockets import emit_mesa_actualizada

                emit_mesa_actualizada(id_local, pedido.id_mesa, "disponible")

        return jsonify(
            {
                "message": "Estado del pedido actualizado",
                "pedido": {"id": pedido.id, "estado": pedido.estado.value},
            }
        ), 200
    finally:
        db.close()


@pedidos_bp.route("/<int:pedido_id>/pago", methods=["POST"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente", "mesero")
def registrar_pago(pedido_id, user_id, user_rol, id_local):
    """
    Registrar pago de un pedido.

    Body:
        { "metodo": "efectivo", "monto": 15000 }
    """
    try:
        data = RegistrarPagoSchema(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": "Datos inválidos", "details": e.errors()}), 400

    db = get_session()
    try:
        # Verificar que el pedido existe y pertenece al local
        stmt = select(Pedido).where(Pedido.id == pedido_id, Pedido.id_local == id_local)
        pedido = db.execute(stmt).scalar_one_or_none()

        if not pedido:
            return jsonify({"error": "Pedido no encontrado"}), 404

        # Verificar que el pedido esté en estado SERVIDO
        if pedido.estado != EstadoPedidoEnum.SERVIDO:
            return jsonify(
                {
                    "error": "Solo se puede registrar pago de pedidos servidos",
                    "estado_actual": pedido.estado.value if pedido.estado else None,
                }
            ), 400

        # Verificar si ya existe un pago para este pedido
        stmt_pago = select(Pago).where(Pago.id_pedido == pedido.id)
        pago_existente = db.execute(stmt_pago).scalar_one_or_none()

        if pago_existente:
            return jsonify(
                {"error": "Ya existe un pago registrado para este pedido"}
            ), 400

        # Crear registro de pago con estado COBRADO
        nuevo_pago = Pago(
            id_pedido=pedido.id,
            creado_por=user_id,
            metodo=data.metodo,
            estado=EstadoPagoEnum.COBRADO,
            monto=data.monto,
        )
        db.add(nuevo_pago)
        db.commit()
        db.refresh(nuevo_pago)

        return jsonify(
            {
                "message": "Pago registrado exitosamente",
                "pago": {
                    "id": nuevo_pago.id,
                    "metodo": nuevo_pago.metodo.value,
                    "estado": nuevo_pago.estado.value,
                    "monto": nuevo_pago.monto,
                },
            }
        ), 201
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


@pedidos_bp.route("/historial", methods=["GET"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente", "mesero")
def obtener_historial_local(user_id, user_rol, id_local):
    """
    Obtiene el historial de pedidos completados y cancelados del local.
    Disponible para gerentes y meseros.
    """
    db = get_session()

    try:
        # Parámetros de filtrado
        estado_filter = request.args.get("estado")  # completado, cancelado, o ambos
        fecha_desde = request.args.get("fecha_desde")  # formato: YYYY-MM-DD
        fecha_hasta = request.args.get("fecha_hasta")  # formato: YYYY-MM-DD
        mesa_id = request.args.get("mesa_id")
        limit = request.args.get("limit", 50, type=int)  # límite de resultados

        # Query base - pedidos completados o cancelados
        estados_validos = [EstadoPedidoEnum.COMPLETADO, EstadoPedidoEnum.CANCELADO]

        if estado_filter:
            if estado_filter == "completado":
                estados_validos = [EstadoPedidoEnum.COMPLETADO]
            elif estado_filter == "cancelado":
                estados_validos = [EstadoPedidoEnum.CANCELADO]

        stmt = (
            select(Pedido)
            .options(
                joinedload(Pedido.qr),
                joinedload(Pedido.mesa),
                joinedload(Pedido.usuario),
                joinedload(Pedido.cuentas).joinedload(Cuenta.producto),
                joinedload(Pedido.pagos),
            )
            .where(Pedido.id_local == id_local, Pedido.estado.in_(estados_validos))
        )

        # Filtros opcionales
        if fecha_desde:
            try:
                fecha_desde_dt = datetime.strptime(fecha_desde, "%Y-%m-%d")
                stmt = stmt.where(Pedido.creado_el >= fecha_desde_dt)
            except ValueError:
                pass

        if fecha_hasta:
            try:
                fecha_hasta_dt = datetime.strptime(fecha_hasta, "%Y-%m-%d")
                # Agregar 1 día para incluir todo el día especificado
                fecha_hasta_dt = fecha_hasta_dt + timedelta(days=1)
                stmt = stmt.where(Pedido.creado_el < fecha_hasta_dt)
            except ValueError:
                pass

        if mesa_id:
            stmt = stmt.where(Pedido.id_mesa == int(mesa_id))

        stmt = stmt.order_by(Pedido.actualizado_el.desc()).limit(limit)

        pedidos = db.execute(stmt).scalars().unique().all()

        historial = []
        for pedido in pedidos:
            # Calcular productos del pedido
            productos = []
            for cuenta in pedido.cuentas:
                productos.append(
                    {
                        "id": cuenta.producto.id if cuenta.producto else None,
                        "nombre": cuenta.producto.nombre
                        if cuenta.producto
                        else "Producto eliminado",
                        "cantidad": cuenta.cantidad,
                        "precio": cuenta.producto.precio if cuenta.producto else 0,
                        "observaciones": cuenta.observaciones,
                    }
                )

            # Obtener información del pago
            pago_info = None
            if pedido.pagos:
                pago = pedido.pagos[0]  # Tomar el primer pago
                pago_info = {
                    "metodo": pago.metodo.value if pago.metodo else None,
                    "monto": pago.monto,
                    "estado": pago.estado.value if pago.estado else None,
                    "fecha": pago.creado_el.isoformat() if pago.creado_el else None,
                }

            historial.append(
                {
                    "pedido_id": pedido.id,
                    "qr_codigo": pedido.qr.codigo if pedido.qr else None,
                    "estado": pedido.estado.value if pedido.estado else None,
                    "fecha_creacion": (
                        pedido.creado_el.isoformat() if pedido.creado_el else None
                    ),
                    "fecha_completado": (
                        pedido.actualizado_el.isoformat()
                        if pedido.actualizado_el
                        else None
                    ),
                    "total": pedido.total,
                    "num_personas": pedido.num_personas,
                    "mesa": {
                        "id": pedido.mesa.id if pedido.mesa else None,
                        "nombre": pedido.mesa.nombre if pedido.mesa else None,
                    },
                    "cliente": {
                        "id": pedido.usuario.id if pedido.usuario else None,
                        "nombre": pedido.usuario.nombre if pedido.usuario else None,
                        "correo": pedido.usuario.correo if pedido.usuario else None,
                    },
                    "productos": productos,
                    "pago": pago_info,
                }
            )

        return jsonify({"historial": historial, "total": len(historial)}), 200

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()
