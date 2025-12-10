"""
Rutas para gestion de mesas del local
Prefix: /api/empresa/mesas/*
"""

from flask import Blueprint, jsonify, request
from pydantic import BaseModel, ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from database import get_session
from models.models import (
    Cuenta,
    Encomienda,
    EncomiendaCuenta,
    EstadoMesaEnum,
    EstadoPedidoEnum,
    Mesa,
    Pedido,
    QRDinamico,
)
from routes.empresa import requerir_empleado, requerir_roles_empresa
from utils.jwt_helper import requerir_auth
from websockets import emit_estado_pedido, emit_mesa_actualizada

mesas_bp = Blueprint("mesas", __name__, url_prefix="/mesas")


# ============================================
# SCHEMAS
# ============================================


class MesaCreateSchema(BaseModel):
    nombre: str
    capacidad: int
    descripcion: str | None = None


class MesaUpdateSchema(BaseModel):
    nombre: str | None = None
    capacidad: int | None = None
    descripcion: str | None = None


class MesaEstadoSchema(BaseModel):
    estado: EstadoMesaEnum


class MesaOrdenItemSchema(BaseModel):
    id: int
    orden: int


class MesasOrdenSchema(BaseModel):
    mesas: list[MesaOrdenItemSchema]


class GenerarQRSchema(BaseModel):
    num_personas: int


# ============================================
# ENDPOINTS
# ============================================


@mesas_bp.route("/", methods=["GET"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente", "mesero")
def listar_mesas(user_id, user_rol, id_local):
    """Listar todas las mesas del local"""
    from models.models import EstadoMesaEnum, Reserva, ReservaMesa

    db = get_session()
    try:
        stmt = select(Mesa).where(
            Mesa.id_local == id_local, Mesa.eliminado_el.is_(None)
        )
        mesas = db.execute(stmt).scalars().all()

        result = []
        for mesa in mesas:
            pedidos_count = len(
                [p for p in mesa.pedidos if p.estado not in ["completado", "cancelado"]]
            )

            # Obtener num_personas según el estado de la mesa
            num_personas = None
            pedido_activo = None

            if mesa.estado == EstadoMesaEnum.OCUPADA:
                # Buscar pedido activo de esta mesa
                pedido_activo = next(
                    (
                        p
                        for p in mesa.pedidos
                        if p.estado
                        not in [EstadoPedidoEnum.COMPLETADO, EstadoPedidoEnum.CANCELADO]
                    ),
                    None,
                )
                if pedido_activo:
                    num_personas = pedido_activo.num_personas

            elif mesa.estado == EstadoMesaEnum.RESERVADA:
                # Buscar reserva activa de esta mesa
                stmt_reserva = (
                    select(Reserva)
                    .join(ReservaMesa)
                    .where(
                        ReservaMesa.id_mesa == mesa.id,
                        Reserva.estado.in_(["pendiente", "confirmada"]),
                    )
                    .order_by(Reserva.fecha_reserva.desc())
                    .limit(1)
                )
                reserva = db.execute(stmt_reserva).scalar_one_or_none()
                if reserva:
                    num_personas = reserva.num_personas

            # Obtener expiracion del pedido activo (para mesas ocupadas)
            expiracion = None
            if mesa.estado == EstadoMesaEnum.OCUPADA and pedido_activo:
                expiracion = (
                    pedido_activo.expiracion.isoformat()
                    if pedido_activo.expiracion
                    else None
                )

            result.append(
                {
                    "id": mesa.id,
                    "id_local": mesa.id_local,
                    "nombre": mesa.nombre,
                    "descripcion": mesa.descripcion,
                    "capacidad": mesa.capacidad,
                    "orden": mesa.orden,
                    "estado": mesa.estado.value if mesa.estado else "disponible",
                    "pedidos_count": pedidos_count,
                    "num_personas": num_personas,
                    "expiracion": expiracion,
                }
            )

        return jsonify(result), 200
    finally:
        db.close()


@mesas_bp.route("/orden", methods=["PUT"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente", "mesero")
def actualizar_orden_mesas(user_id, user_rol, id_local):
    """Actualizar orden de multiples mesas (Drag and Drop)"""
    try:
        data = MesasOrdenSchema(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": "Datos invalidos", "details": e.errors()}), 400

    db = get_session()
    try:
        for item in data.mesas:
            stmt = select(Mesa).where(Mesa.id == item.id, Mesa.id_local == id_local)
            mesa = db.execute(stmt).scalar_one_or_none()
            if mesa:
                mesa.orden = item.orden

        db.commit()
        return jsonify({"message": "Orden actualizado exitosamente"}), 200
    finally:
        db.close()


@mesas_bp.route("/", methods=["POST"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente", "mesero")
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

        # Obtener el orden maximo actual para asignar al final
        stmt_max = select(Mesa).where(Mesa.id_local == id_local)
        mesas_existentes = db.execute(stmt_max).scalars().all()
        max_orden = max((m.orden for m in mesas_existentes), default=-1)

        nueva_mesa = Mesa(
            id_local=id_local,
            nombre=data.nombre,
            descripcion=data.descripcion,
            capacidad=data.capacidad,
            orden=max_orden + 1,
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
                    "descripcion": nueva_mesa.descripcion,
                    "capacidad": nueva_mesa.capacidad,
                    "orden": nueva_mesa.orden,
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

        if data.descripcion is not None:
            mesa.descripcion = data.descripcion

        db.commit()

        return jsonify(
            {
                "message": "Mesa actualizada",
                "mesa": {
                    "id": mesa.id,
                    "nombre": mesa.nombre,
                    "descripcion": mesa.descripcion,
                    "capacidad": mesa.capacidad,
                    "orden": mesa.orden,
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
@requerir_roles_empresa("gerente", "mesero")
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

        # Soft Delete
        mesa.eliminado_el = func.now()
        # Cambiar estado a fuera de servicio para evitar asignar pedidos si algo falla
        mesa.estado = EstadoMesaEnum.FUERA_DE_SERVICIO

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

    db = get_session()
    try:
        # Validar request body
        try:
            data = request.get_json() or {}
            qr_data = GenerarQRSchema(**data)
        except ValidationError as e:
            return jsonify({"error": "Datos inválidos", "details": e.errors()}), 400

        stmt = select(Mesa).where(Mesa.id == mesa_id, Mesa.id_local == id_local)
        mesa = db.execute(stmt).scalar_one_or_none()

        if not mesa:
            return jsonify({"error": "Mesa no encontrada"}), 404

        # Verificar si ya hay un QR activo para esta mesa (solo QRs de pedido, no de reserva)
        # que aún no haya sido escaneado (sin pedido asociado)
        stmt_qr = select(QRDinamico).where(
            QRDinamico.id_mesa == mesa_id,
            QRDinamico.activo.is_(True),
            QRDinamico.id_reserva.is_(None),  # Solo QRs de pedido directo
            QRDinamico.id_pedido.is_(None),  # Solo QRs no escaneados aún
        )
        qr_existente = db.execute(stmt_qr).scalar_one_or_none()

        if qr_existente:
            # Ya existe un QR activo no escaneado - reutilizarlo
            # Actualizar num_personas si es diferente
            if qr_existente.num_personas != qr_data.num_personas:
                qr_existente.num_personas = qr_data.num_personas
                db.commit()
                db.refresh(qr_existente)

            # Retornar QR existente (actualizado o no)
            return jsonify(
                {
                    "message": "QR activo existente",
                    "qr": {
                        "codigo": qr_existente.codigo,
                        "mesa_id": mesa.id,
                        "mesa_nombre": mesa.nombre,
                        "local_id": id_local,
                        "url": f"/pedido?qr={qr_existente.codigo}",
                    },
                }
            ), 200

        # Generar nuevo codigo unico
        codigo = f"QR-{secrets.token_urlsafe(8).upper()}"

        # Sin expiracion inicial - el QR no expira hasta que se escanee
        # La expiracion se maneja en el Pedido, no en el QR

        # Crear nuevo QR
        # CASO 2 - PEDIDO: Tiene num_personas, NO tiene id_reserva (NULL)
        # id_pedido es NULL al inicio, se llena cuando el cliente escanea el QR
        nuevo_qr = QRDinamico(
            id_mesa=mesa_id,
            id_usuario=user_id,
            id_reserva=None,  # NULL - esto es para pedidos directos, no reservas
            codigo=codigo,
            expiracion=None,  # Sin expiracion inicial
            activo=True,
            num_personas=qr_data.num_personas,  # Guardado para transferir al Pedido
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
                joinedload(Mesa.pedidos).joinedload(Pedido.usuario),
                joinedload(Mesa.pedidos)
                .joinedload(Pedido.cuentas)
                .joinedload(Cuenta.producto),
                joinedload(Mesa.pedidos)
                .joinedload(Pedido.encomiendas)
                .joinedload(Encomienda.cuentas_encomienda)
                .joinedload(EncomiendaCuenta.cuenta)
                .joinedload(Cuenta.producto),
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

                cliente_info = None
                if pedido.usuario:
                    cliente_info = {
                        "id": pedido.usuario.id,
                        "nombre": pedido.usuario.nombre,
                        "email": pedido.usuario.correo,
                    }

                # Ordenar encomiendas por fecha de creación
                encomiendas_ordenadas = sorted(
                    pedido.encomiendas, key=lambda e: e.creado_el or ""
                )
                encomiendas_list = []
                for idx, enc in enumerate(encomiendas_ordenadas):
                    items = []
                    for ec in enc.cuentas_encomienda:
                        cuenta = ec.cuenta
                        items.append(
                            {
                                "id": cuenta.id,
                                "producto": cuenta.producto.nombre
                                if cuenta.producto
                                else "Producto eliminado",
                                "cantidad": cuenta.cantidad,
                                "precio_unitario": cuenta.producto.precio
                                if cuenta.producto
                                else 0,
                                "observaciones": cuenta.observaciones,
                            }
                        )
                    encomiendas_list.append(
                        {
                            "id": enc.id,
                            "estado": enc.estado.value if enc.estado else None,
                            "nombre": "Pedido" if idx == 0 else f"Pedido Extra #{idx}",
                            "items": items,
                            "creado_el": enc.creado_el.isoformat()
                            if enc.creado_el
                            else None,
                        }
                    )

                pedido_activo = {
                    "id": pedido.id,
                    "estado": pedido.estado.value if pedido.estado else None,
                    "total": pedido.total,
                    "creado_el": pedido.creado_el.isoformat()
                    if pedido.creado_el
                    else None,
                    "expiracion": pedido.expiracion.isoformat()
                    if pedido.expiracion
                    else None,
                    "lineas": lineas,
                    "cliente": cliente_info,
                    "encomiendas": encomiendas_list,
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
        stmt_pedidos = (
            select(Pedido)
            .options(joinedload(Pedido.qr))
            .where(
                Pedido.id_mesa == mesa_id,
                Pedido.id_local == id_local,
                Pedido.estado.not_in(
                    [EstadoPedidoEnum.COMPLETADO, EstadoPedidoEnum.CANCELADO]
                ),
            )
        )
        pedidos_activos = db.execute(stmt_pedidos).scalars().all()

        pedidos_cancelados = 0
        for pedido in pedidos_activos:
            pedido.estado = EstadoPedidoEnum.CANCELADO
            # Desactivar QR asociado al pedido
            if pedido.qr:
                pedido.qr.activo = False
            pedidos_cancelados += 1

            # Emitir evento WebSocket de cancelación
            emit_estado_pedido(id_local, pedido.id, EstadoPedidoEnum.CANCELADO.value)

        # Desactivar TODOS los QRs activos de esta mesa (incluyendo los no escaneados)
        stmt_qrs = select(QRDinamico).where(
            QRDinamico.id_mesa == mesa_id,
            QRDinamico.activo.is_(True),
        )
        qrs_activos = db.execute(stmt_qrs).scalars().all()
        for qr in qrs_activos:
            qr.activo = False

        # Cambiar estado de la mesa a disponible
        mesa.estado = EstadoMesaEnum.DISPONIBLE
        db.commit()

        # Emitir evento de actualización de mesa
        emit_mesa_actualizada(id_local, mesa.id, EstadoMesaEnum.DISPONIBLE.value)

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
