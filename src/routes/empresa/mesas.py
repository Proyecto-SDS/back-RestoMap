"""
Rutas para gestion de mesas del local
Prefix: /api/empresa/mesas/*
"""

from flask import Blueprint, jsonify, request
from pydantic import BaseModel, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from database import get_session
from models.models import (
    Cuenta,
    EstadoMesaEnum,
    EstadoPedidoEnum,
    Mesa,
    Pedido,
)
from routes.empresa import requerir_empleado, requerir_roles_empresa
from utils.jwt_helper import requerir_auth

mesas_bp = Blueprint("mesas", __name__, url_prefix="/mesas")


# ============================================
# SCHEMAS
# ============================================


class MesaCreateSchema(BaseModel):
    nombre: str
    capacidad: int


class MesaUpdateSchema(BaseModel):
    nombre: str | None = None
    capacidad: int | None = None


class MesaEstadoSchema(BaseModel):
    estado: EstadoMesaEnum


# ============================================
# ENDPOINTS
# ============================================


@mesas_bp.route("/", methods=["GET"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente", "mesero")
def listar_mesas(user_id, user_rol, id_local):
    """Listar todas las mesas del local"""
    db = get_session()
    try:
        stmt = select(Mesa).where(Mesa.id_local == id_local)
        mesas = db.execute(stmt).scalars().all()

        result = []
        for mesa in mesas:
            pedidos_count = len(
                [p for p in mesa.pedidos if p.estado not in ["completado", "cancelado"]]
            )
            result.append(
                {
                    "id": mesa.id,
                    "id_local": mesa.id_local,
                    "nombre": mesa.nombre,
                    "capacidad": mesa.capacidad,
                    "estado": mesa.estado.value if mesa.estado else "disponible",
                    "pedidos_count": pedidos_count,
                }
            )

        return jsonify(result), 200
    finally:
        db.close()


@mesas_bp.route("/", methods=["POST"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente")
def crear_mesa(user_id, user_rol, id_local):
    """Crear una nueva mesa"""
    try:
        data = MesaCreateSchema(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": "Datos inválidos", "details": e.errors()}), 400

    db = get_session()
    try:
        # Verificar nombre único en el local
        stmt = select(Mesa).where(Mesa.id_local == id_local, Mesa.nombre == data.nombre)
        existing = db.execute(stmt).scalar_one_or_none()

        if existing:
            return jsonify(
                {"error": f"Ya existe una mesa con el nombre '{data.nombre}'"}
            ), 400

        nueva_mesa = Mesa(
            id_local=id_local,
            nombre=data.nombre,
            capacidad=data.capacidad,
            estado=EstadoMesaEnum.DISPONIBLE,
        )
        db.add(nueva_mesa)
        db.commit()
        db.refresh(nueva_mesa)

        return jsonify(
            {
                "message": "Mesa creada exitosamente",
                "mesa": {
                    "id": nueva_mesa.id,
                    "nombre": nueva_mesa.nombre,
                    "capacidad": nueva_mesa.capacidad,
                    "estado": nueva_mesa.estado.value,
                },
            }
        ), 201
    finally:
        db.close()


@mesas_bp.route("/<int:mesa_id>", methods=["PUT"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente", "mesero")
def actualizar_mesa(mesa_id, user_id, user_rol, id_local):
    """Actualizar datos de una mesa"""
    try:
        data = MesaUpdateSchema(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": "Datos inválidos", "details": e.errors()}), 400

    db = get_session()
    try:
        stmt = select(Mesa).where(Mesa.id == mesa_id, Mesa.id_local == id_local)
        mesa = db.execute(stmt).scalar_one_or_none()

        if not mesa:
            return jsonify({"error": "Mesa no encontrada"}), 404

        if data.nombre is not None:
            stmt_check = select(Mesa).where(
                Mesa.id_local == id_local,
                Mesa.nombre == data.nombre,
                Mesa.id != mesa_id,
            )
            existing = db.execute(stmt_check).scalar_one_or_none()
            if existing:
                return jsonify(
                    {"error": f"Ya existe una mesa con el nombre '{data.nombre}'"}
                ), 400
            mesa.nombre = data.nombre

        if data.capacidad is not None:
            mesa.capacidad = data.capacidad

        db.commit()

        return jsonify(
            {
                "message": "Mesa actualizada",
                "mesa": {
                    "id": mesa.id,
                    "nombre": mesa.nombre,
                    "capacidad": mesa.capacidad,
                    "estado": mesa.estado.value if mesa.estado else "disponible",
                },
            }
        ), 200
    finally:
        db.close()


@mesas_bp.route("/<int:mesa_id>/estado", methods=["PATCH"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente", "mesero")
def cambiar_estado_mesa(mesa_id, user_id, user_rol, id_local):
    """Cambiar estado de una mesa"""
    try:
        data = MesaEstadoSchema(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": "Datos inválidos", "details": e.errors()}), 400

    db = get_session()
    try:
        stmt = select(Mesa).where(Mesa.id == mesa_id, Mesa.id_local == id_local)
        mesa = db.execute(stmt).scalar_one_or_none()

        if not mesa:
            return jsonify({"error": "Mesa no encontrada"}), 404

        mesa.estado = data.estado
        db.commit()

        return jsonify(
            {
                "message": "Estado de mesa actualizado",
                "mesa": {
                    "id": mesa.id,
                    "nombre": mesa.nombre,
                    "estado": mesa.estado.value,
                },
            }
        ), 200
    finally:
        db.close()


@mesas_bp.route("/<int:mesa_id>", methods=["DELETE"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente")
def eliminar_mesa(mesa_id, user_id, user_rol, id_local):
    """Eliminar una mesa"""
    db = get_session()
    try:
        stmt = select(Mesa).where(Mesa.id == mesa_id, Mesa.id_local == id_local)
        mesa = db.execute(stmt).scalar_one_or_none()

        if not mesa:
            return jsonify({"error": "Mesa no encontrada"}), 404

        pedidos_activos = [
            p for p in mesa.pedidos if p.estado not in ["completado", "cancelado"]
        ]
        if pedidos_activos:
            return jsonify(
                {"error": "No se puede eliminar una mesa con pedidos activos"}
            ), 400

        db.delete(mesa)
        db.commit()

        return jsonify({"message": "Mesa eliminada exitosamente"}), 200
    finally:
        db.close()


@mesas_bp.route("/<int:mesa_id>/qr", methods=["POST"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente", "mesero")
def generar_qr_mesa(mesa_id, user_id, user_rol, id_local):
    """Generar QR dinámico para una mesa - crea registro en BD"""
    import secrets
    from datetime import datetime, timedelta

    from models.models import QRDinamico

    db = get_session()
    try:
        stmt = select(Mesa).where(Mesa.id == mesa_id, Mesa.id_local == id_local)
        mesa = db.execute(stmt).scalar_one_or_none()

        if not mesa:
            return jsonify({"error": "Mesa no encontrada"}), 404

        # Verificar si ya hay un QR activo para esta mesa
        stmt_qr = select(QRDinamico).where(
            QRDinamico.id_mesa == mesa_id,
            QRDinamico.activo.is_(True),
        )
        qr_existente = db.execute(stmt_qr).scalar_one_or_none()

        if qr_existente:
            # Verificar si no ha expirado
            if qr_existente.expiracion and qr_existente.expiracion > datetime.now(
                qr_existente.expiracion.tzinfo
            ):
                # Retornar QR existente
                return jsonify(
                    {
                        "message": "QR activo existente",
                        "qr": {
                            "codigo": qr_existente.codigo,
                            "mesa_id": mesa.id,
                            "mesa_nombre": mesa.nombre,
                            "local_id": id_local,
                            "expiracion": qr_existente.expiracion.isoformat(),
                            "url": f"/pedido?qr={qr_existente.codigo}",
                        },
                    }
                ), 200
            else:
                # Desactivar QR expirado
                qr_existente.activo = False

        # Generar nuevo codigo unico
        codigo = f"QR-{secrets.token_urlsafe(8).upper()}"

        # Expiracion: 4 horas desde ahora
        expiracion = datetime.now() + timedelta(hours=4)

        # Crear nuevo QR
        nuevo_qr = QRDinamico(
            id_mesa=mesa_id,
            id_usuario=user_id,
            codigo=codigo,
            expiracion=expiracion,
            activo=True,
        )
        db.add(nuevo_qr)
        db.commit()
        db.refresh(nuevo_qr)

        return jsonify(
            {
                "message": "QR generado exitosamente",
                "qr": {
                    "codigo": nuevo_qr.codigo,
                    "mesa_id": mesa.id,
                    "mesa_nombre": mesa.nombre,
                    "local_id": id_local,
                    "expiracion": expiracion.isoformat(),
                    "url": f"/pedido?qr={nuevo_qr.codigo}",
                },
            }
        ), 201
    finally:
        db.close()


@mesas_bp.route("/<int:mesa_id>", methods=["GET"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente", "mesero")
def obtener_mesa(mesa_id, user_id, user_rol, id_local):
    """Obtener detalle completo de una mesa incluyendo pedido activo"""
    db = get_session()
    try:
        stmt = (
            select(Mesa)
            .options(
                joinedload(Mesa.pedidos)
                .joinedload(Pedido.cuentas)
                .joinedload(Cuenta.producto)
            )
            .where(Mesa.id == mesa_id, Mesa.id_local == id_local)
        )
        mesa = db.execute(stmt).unique().scalar_one_or_none()

        if not mesa:
            return jsonify({"error": "Mesa no encontrada"}), 404

        # Buscar pedido activo (no completado ni cancelado)
        pedido_activo = None
        for pedido in mesa.pedidos:
            if pedido.estado not in [
                EstadoPedidoEnum.COMPLETADO,
                EstadoPedidoEnum.CANCELADO,
            ]:
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
                pedido_activo = {
                    "id": pedido.id,
                    "estado": pedido.estado.value if pedido.estado else None,
                    "total": pedido.total,
                    "creado_el": pedido.creado_el.isoformat()
                    if pedido.creado_el
                    else None,
                    "lineas": lineas,
                }
                break

        return jsonify(
            {
                "id": mesa.id,
                "nombre": mesa.nombre,
                "capacidad": mesa.capacidad,
                "estado": mesa.estado.value if mesa.estado else "disponible",
                "pedido_activo": pedido_activo,
            }
        ), 200
    finally:
        db.close()


@mesas_bp.route("/<int:mesa_id>/pedido-activo", methods=["GET"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente", "mesero", "cocinero", "bartender")
def pedido_activo_mesa(mesa_id, user_id, user_rol, id_local):
    """Obtener el pedido activo de una mesa"""
    db = get_session()
    try:
        stmt = select(Mesa).where(Mesa.id == mesa_id, Mesa.id_local == id_local)
        mesa = db.execute(stmt).scalar_one_or_none()

        if not mesa:
            return jsonify({"error": "Mesa no encontrada"}), 404

        # Buscar pedido activo
        stmt_pedido = (
            select(Pedido)
            .options(joinedload(Pedido.cuentas).joinedload(Cuenta.producto))
            .where(
                Pedido.id_mesa == mesa_id,
                Pedido.id_local == id_local,
                Pedido.estado.not_in(
                    [EstadoPedidoEnum.COMPLETADO, EstadoPedidoEnum.CANCELADO]
                ),
            )
            .order_by(Pedido.creado_el.desc())
        )
        pedido = db.execute(stmt_pedido).unique().scalar_one_or_none()

        if not pedido:
            return jsonify({"pedido": None}), 200

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
                "pedido": {
                    "id": pedido.id,
                    "estado": pedido.estado.value if pedido.estado else None,
                    "total": pedido.total,
                    "creado_el": pedido.creado_el.isoformat()
                    if pedido.creado_el
                    else None,
                    "lineas": lineas,
                }
            }
        ), 200
    finally:
        db.close()


@mesas_bp.route("/<int:mesa_id>/cancelar", methods=["POST"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente", "mesero")
def cancelar_mesa(mesa_id, user_id, user_rol, id_local):
    """Cancelar mesa ocupada - cancela pedido activo y libera mesa"""
    db = get_session()
    try:
        stmt = select(Mesa).where(Mesa.id == mesa_id, Mesa.id_local == id_local)
        mesa = db.execute(stmt).scalar_one_or_none()

        if not mesa:
            return jsonify({"error": "Mesa no encontrada"}), 404

        # Cancelar todos los pedidos activos de la mesa
        stmt_pedidos = select(Pedido).where(
            Pedido.id_mesa == mesa_id,
            Pedido.id_local == id_local,
            Pedido.estado.not_in(
                [EstadoPedidoEnum.COMPLETADO, EstadoPedidoEnum.CANCELADO]
            ),
        )
        pedidos_activos = db.execute(stmt_pedidos).scalars().all()

        pedidos_cancelados = 0
        for pedido in pedidos_activos:
            pedido.estado = EstadoPedidoEnum.CANCELADO
            pedidos_cancelados += 1

        # Cambiar estado de la mesa a disponible
        mesa.estado = EstadoMesaEnum.DISPONIBLE
        db.commit()

        return jsonify(
            {
                "message": "Mesa cancelada exitosamente",
                "mesa": {
                    "id": mesa.id,
                    "nombre": mesa.nombre,
                    "estado": mesa.estado.value,
                },
                "pedidos_cancelados": pedidos_cancelados,
            }
        ), 200
    finally:
        db.close()
