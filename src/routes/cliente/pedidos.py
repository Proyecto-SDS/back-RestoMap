"""
Rutas de cliente para pedidos mediante QR
Prefix: /api/cliente/*
"""

import contextlib
import traceback
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from database import get_session
from models import (
    Cuenta,
    Encomienda,
    EstadoEncomiendaEnum,
    EstadoMesaEnum,
    EstadoPedidoEnum,
    EstadoProductoEnum,
    Local,
    Pedido,
    Producto,
    QRDinamico,
)
from utils.jwt_helper import requerir_auth_persona
from websockets import (
    emit_mesa_actualizada,
    emit_nueva_encomienda,
    emit_qr_escaneado,
)

cliente_bp = Blueprint("cliente", __name__, url_prefix="/api/cliente")


@cliente_bp.route("/qr/validar", methods=["POST"])
@requerir_auth_persona
def validar_qr(user_id):
    """
    Valida un codigo QR y crea/obtiene el pedido asociado.

    Body:
        { "codigo": "QR-XXXX" }

    Returns:
        Info de la mesa, local y pedido activo
    """
    data = request.get_json()
    if not data or "codigo" not in data:
        return jsonify({"error": "Codigo QR requerido"}), 400

    codigo = data["codigo"]
    db = get_session()

    try:
        # Buscar QR
        stmt = (
            select(QRDinamico)
            .options(
                joinedload(QRDinamico.mesa),
                joinedload(QRDinamico.pedido),
            )
            .where(QRDinamico.codigo == codigo)
        )
        qr = db.execute(stmt).scalar_one_or_none()

        if not qr:
            return jsonify({"error": "Codigo QR no encontrado"}), 404

        # Verificar que este activo
        if not qr.activo:
            return jsonify({"error": "Este codigo QR ya no esta activo"}), 400

        # Verificar expiracion
        if qr.expiracion and qr.expiracion < datetime.now(qr.expiracion.tzinfo):
            # Marcar QR como inactivo si expiró
            qr.activo = False
            db.commit()
            return jsonify({"error": "Este codigo QR ha expirado"}), 400

        # VALIDACIÓN: QRs de reserva solo pueden usarse después de confirmación
        if qr.id_reserva and not qr.id_pedido:
            return jsonify(
                {
                    "error": "Este QR corresponde a una reserva. Debe ser confirmada por el personal del restaurante."
                }
            ), 400

        mesa = qr.mesa
        if not mesa:
            return jsonify({"error": "Mesa no encontrada"}), 404

        # Obtener local
        local = db.query(Local).filter(Local.id == mesa.id_local).first()
        if not local:
            return jsonify({"error": "Local no encontrado"}), 404

        # Buscar o crear pedido activo
        pedido = qr.pedido

        if not pedido:
            # Determinar num_personas según el tipo de QR
            num_personas = None

            if qr.id_reserva:
                # CASO 1 - RESERVA: Obtener num_personas de la Reserva
                from models import Reserva

                reserva = db.query(Reserva).filter(Reserva.id == qr.id_reserva).first()
                if reserva:
                    num_personas = reserva.num_personas
            else:
                # CASO 2 - PEDIDO: Obtener num_personas del QR
                num_personas = qr.num_personas

            # Crear nuevo pedido
            pedido = Pedido(
                id_local=mesa.id_local,
                id_mesa=mesa.id,
                id_usuario=user_id,
                id_qr=qr.id,
                creado_por=user_id,
                estado=EstadoPedidoEnum.INICIADO,
                total=0,
                num_personas=num_personas,
            )
            db.add(pedido)
            db.flush()

            # Actualizar QR con pedido
            qr.id_pedido = pedido.id

            # CASO 2 - PEDIDO: Extender expiración a 2 horas al escanear
            # (solo si no es reserva)
            if not qr.id_reserva:
                qr.expiracion = datetime.now() + timedelta(hours=2)

            # Cambiar estado de mesa a ocupada
            mesa.estado = EstadoMesaEnum.OCUPADA

            db.commit()

            # Emitir evento WebSocket - QR escaneado
            try:
                emit_qr_escaneado(mesa.id_local, mesa.id, pedido.id)
                emit_mesa_actualizada(mesa.id_local, mesa.id, "ocupada")
            except Exception:
                pass  # No fallar si websocket no esta disponible

        return jsonify(
            {
                "success": True,
                "qr_codigo": codigo,
                "mesa": {
                    "id": mesa.id,
                    "nombre": mesa.nombre,
                    "capacidad": mesa.capacidad,
                },
                "local": {
                    "id": local.id,
                    "nombre": local.nombre,
                },
                "pedido": {
                    "id": pedido.id,
                    "estado": pedido.estado.value if pedido.estado else "iniciado",
                    "total": pedido.total or 0,
                },
            }
        ), 200

    except Exception as e:
        traceback.print_exc()
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@cliente_bp.route("/pedido/<codigo>/menu", methods=["GET"])
@requerir_auth_persona
def obtener_menu(codigo, user_id):
    """
    Obtiene el menu del local asociado al QR.
    Solo muestra productos disponibles.
    """
    db = get_session()

    try:
        # Buscar QR y obtener local
        stmt = (
            select(QRDinamico)
            .options(joinedload(QRDinamico.mesa))
            .where(QRDinamico.codigo == codigo, QRDinamico.activo.is_(True))
        )
        qr = db.execute(stmt).scalar_one_or_none()

        if not qr or not qr.mesa:
            return jsonify({"error": "QR invalido o expirado"}), 404

        id_local = qr.mesa.id_local

        # Obtener productos disponibles agrupados por categoria
        stmt_productos = (
            select(Producto)
            .options(joinedload(Producto.categoria), joinedload(Producto.fotos))
            .where(
                Producto.id_local == id_local,
                Producto.estado == EstadoProductoEnum.DISPONIBLE,
            )
            .order_by(Producto.id_categoria, Producto.nombre)
        )
        productos = db.execute(stmt_productos).scalars().unique().all()

        # Agrupar por categoria
        categorias_dict = {}
        for producto in productos:
            cat_id = producto.id_categoria or 0
            cat_nombre = (
                producto.categoria.nombre if producto.categoria else "Sin categoria"
            )

            if cat_id not in categorias_dict:
                categorias_dict[cat_id] = {
                    "id": cat_id,
                    "nombre": cat_nombre,
                    "productos": [],
                }

            # Obtener imagen
            imagen = ""
            if producto.fotos:
                imagen = producto.fotos[0].ruta

            categorias_dict[cat_id]["productos"].append(
                {
                    "id": producto.id,
                    "nombre": producto.nombre,
                    "descripcion": producto.descripcion,
                    "precio": producto.precio,
                    "imagen": imagen,
                }
            )

        return jsonify({"categorias": list(categorias_dict.values())}), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@cliente_bp.route("/pedido/<codigo>/agregar", methods=["POST"])
@requerir_auth_persona
def agregar_productos(codigo, user_id):
    """
    Agrega productos al pedido (crea una nueva Encomienda).

    Body:
        {
            "productos": [
                {"id": 1, "cantidad": 2, "nota": "sin cebolla"},
                {"id": 2, "cantidad": 1}
            ]
        }
    """
    data = request.get_json()
    if not data or "productos" not in data:
        return jsonify({"error": "Lista de productos requerida"}), 400

    productos_lista = data["productos"]
    if not productos_lista:
        return jsonify({"error": "Debe agregar al menos un producto"}), 400

    db = get_session()

    try:
        # Buscar QR y pedido
        stmt = (
            select(QRDinamico)
            .options(joinedload(QRDinamico.pedido))
            .where(QRDinamico.codigo == codigo, QRDinamico.activo.is_(True))
        )
        qr = db.execute(stmt).scalar_one_or_none()

        if not qr:
            return jsonify({"error": "QR invalido o expirado"}), 404

        pedido = qr.pedido
        if not pedido:
            return jsonify({"error": "No hay pedido activo para este QR"}), 404

        # Verificar que el pedido no este completado o cancelado
        if pedido.estado in [EstadoPedidoEnum.COMPLETADO, EstadoPedidoEnum.CANCELADO]:
            return jsonify({"error": "El pedido ya fue cerrado"}), 400

        # Verificar que el pedido pertenece al usuario
        if pedido.id_usuario != user_id:
            return jsonify(
                {"error": "No tienes permiso para modificar este pedido"}
            ), 403

        # Crear nueva Encomienda
        encomienda = Encomienda(
            id_pedido=pedido.id,
            estado=EstadoEncomiendaEnum.PENDIENTE,
        )
        db.add(encomienda)
        db.flush()

        # Agregar productos (Cuentas)
        total_encomienda = 0
        cuentas_creadas = []

        for item in productos_lista:
            producto_id = item.get("id")
            cantidad = item.get("cantidad", 1)
            nota = item.get("nota", "")

            # Obtener producto
            producto = (
                db.query(Producto)
                .filter(
                    Producto.id == producto_id,
                    Producto.estado == EstadoProductoEnum.DISPONIBLE,
                )
                .first()
            )

            if not producto:
                continue

            # Crear Cuenta (linea de pedido)
            cuenta = Cuenta(
                id_pedido=pedido.id,
                id_producto=producto_id,
                creado_por=user_id,
                cantidad=cantidad,
                observaciones=nota if nota else None,
            )
            db.add(cuenta)
            db.flush()

            # Vincular con encomienda
            from models import EncomiendaCuenta

            enc_cuenta = EncomiendaCuenta(
                id_cuenta=cuenta.id,
                id_encomienda=encomienda.id,
            )
            db.add(enc_cuenta)

            subtotal = producto.precio * cantidad
            total_encomienda += subtotal

            cuentas_creadas.append(
                {
                    "id": cuenta.id,
                    "producto": producto.nombre,
                    "cantidad": cantidad,
                    "precio_unitario": producto.precio,
                    "subtotal": subtotal,
                    "nota": nota,
                }
            )

        # Actualizar total del pedido
        pedido.total = (pedido.total or 0) + total_encomienda

        # Si el pedido estaba en INICIADO, pasar a RECEPCION
        if pedido.estado == EstadoPedidoEnum.INICIADO:
            pedido.estado = EstadoPedidoEnum.RECEPCION

        db.commit()

        # Emitir evento WebSocket - Nueva encomienda
        with contextlib.suppress(Exception):
            emit_nueva_encomienda(
                pedido.mesa.id_local if pedido.mesa else 0,
                {
                    "encomienda_id": encomienda.id,
                    "pedido_id": pedido.id,
                    "mesa_id": pedido.id_mesa,
                    "mesa_nombre": pedido.mesa.nombre if pedido.mesa else "",
                    "estado": encomienda.estado.value,
                    "items": cuentas_creadas,
                    "total": total_encomienda,
                },
            )

        return jsonify(
            {
                "success": True,
                "encomienda": {
                    "id": encomienda.id,
                    "estado": encomienda.estado.value,
                    "items": cuentas_creadas,
                    "total": total_encomienda,
                },
                "pedido_total": pedido.total,
            }
        ), 201

    except Exception as e:
        traceback.print_exc()
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@cliente_bp.route("/pedido/<codigo>/estado", methods=["GET"])
@requerir_auth_persona
def obtener_estado(codigo, user_id):
    """
    Obtiene el estado actual del pedido y todas sus encomiendas.
    """
    db = get_session()

    try:
        # Buscar QR y pedido
        stmt = (
            select(QRDinamico)
            .options(joinedload(QRDinamico.pedido).joinedload(Pedido.encomiendas))
            .where(QRDinamico.codigo == codigo)
        )
        qr = db.execute(stmt).unique().scalar_one_or_none()

        if not qr:
            return jsonify({"error": "QR no encontrado"}), 404

        pedido = qr.pedido
        if not pedido:
            return jsonify({"error": "No hay pedido para este QR"}), 404

        # Obtener encomiendas con sus cuentas
        encomiendas_data = []
        for enc in pedido.encomiendas:
            # Obtener cuentas de esta encomienda
            items = []
            for enc_cuenta in enc.cuentas_encomienda:
                cuenta = enc_cuenta.cuenta
                if cuenta and cuenta.producto:
                    items.append(
                        {
                            "id": cuenta.id,
                            "producto": cuenta.producto.nombre,
                            "cantidad": cuenta.cantidad,
                            "precio_unitario": cuenta.producto.precio,
                            "nota": cuenta.observaciones,
                        }
                    )

            encomiendas_data.append(
                {
                    "id": enc.id,
                    "estado": enc.estado.value if enc.estado else "pendiente",
                    "creado_el": enc.creado_el.isoformat() if enc.creado_el else None,
                    "items": items,
                }
            )

        # Estado general del pedido
        sesion_activa = pedido.estado not in [
            EstadoPedidoEnum.COMPLETADO,
            EstadoPedidoEnum.CANCELADO,
        ]

        return jsonify(
            {
                "pedido": {
                    "id": pedido.id,
                    "estado": pedido.estado.value if pedido.estado else "iniciado",
                    "total": pedido.total or 0,
                    "creado_el": pedido.creado_el.isoformat()
                    if pedido.creado_el
                    else None,
                },
                "encomiendas": encomiendas_data,
                "sesion_activa": sesion_activa,
                "puede_agregar": sesion_activa,
            }
        ), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@cliente_bp.route("/pedido/<codigo>/cuenta/<int:cuenta_id>/nota", methods=["PUT"])
@requerir_auth_persona
def agregar_nota(codigo, cuenta_id, user_id):
    """
    Agrega o actualiza la nota de un producto (cuenta).

    Body:
        { "nota": "sin cebolla, extra salsa" }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Datos requeridos"}), 400

    nota = data.get("nota", "")

    db = get_session()

    try:
        # Verificar QR
        qr = (
            db.query(QRDinamico)
            .filter(
                QRDinamico.codigo == codigo,
                QRDinamico.activo.is_(True),
            )
            .first()
        )

        if not qr or not qr.id_pedido:
            return jsonify({"error": "QR invalido"}), 404

        # Obtener cuenta
        cuenta = (
            db.query(Cuenta)
            .filter(
                Cuenta.id == cuenta_id,
                Cuenta.id_pedido == qr.id_pedido,
            )
            .first()
        )

        if not cuenta:
            return jsonify({"error": "Producto no encontrado en este pedido"}), 404

        # Verificar que el usuario creo esta cuenta
        if cuenta.creado_por != user_id:
            return jsonify(
                {"error": "No tienes permiso para modificar este producto"}
            ), 403

        # Actualizar nota
        cuenta.observaciones = nota if nota else None
        db.commit()

        return jsonify(
            {
                "success": True,
                "cuenta_id": cuenta_id,
                "nota": nota,
            }
        ), 200

    except Exception as e:
        traceback.print_exc()
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@cliente_bp.route("/pedido-activo", methods=["GET"])
@requerir_auth_persona
def obtener_pedido_activo(user_id):
    """
    Obtiene el pedido activo del usuario si existe.
    Retorna el código QR para poder retomar el pedido.

    Returns:
        { "tiene_pedido": true, "qr_codigo": "QR-XXXX", "pedido_id": 123, ... }
        o
        { "tiene_pedido": false }
    """
    db = get_session()

    try:
        # Buscar pedido activo del usuario (no completado ni cancelado)
        stmt = (
            select(Pedido)
            .options(
                joinedload(Pedido.qr),
                joinedload(Pedido.mesa),
                joinedload(Pedido.local),
            )
            .where(
                Pedido.id_usuario == user_id,
                Pedido.estado.notin_(
                    [
                        EstadoPedidoEnum.COMPLETADO,
                        EstadoPedidoEnum.CANCELADO,
                    ]
                ),
            )
            .order_by(Pedido.creado_el.desc())
            .limit(1)
        )
        pedido = db.execute(stmt).scalar_one_or_none()

        if not pedido or not pedido.qr:
            return jsonify({"tiene_pedido": False}), 200

        # Verificar que el QR sigue activo
        if not pedido.qr.activo:
            return jsonify({"tiene_pedido": False}), 200

        return jsonify(
            {
                "tiene_pedido": True,
                "qr_codigo": pedido.qr.codigo,
                "pedido_id": pedido.id,
                "estado": pedido.estado.value if pedido.estado else "iniciado",
                "mesa": {
                    "id": pedido.mesa.id if pedido.mesa else None,
                    "nombre": pedido.mesa.nombre if pedido.mesa else None,
                },
                "local": {
                    "id": pedido.local.id if pedido.local else None,
                    "nombre": pedido.local.nombre if pedido.local else None,
                },
            }
        ), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()
