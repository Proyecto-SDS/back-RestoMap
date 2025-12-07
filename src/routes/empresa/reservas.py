"""
Rutas para gestión de reservas del local
Prefix: /api/empresa/reservas/*
"""

import contextlib

from flask import Blueprint, jsonify, request
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from database import get_session
from models.models import EstadoReservaEnum, Reserva, ReservaMesa
from routes.empresa import requerir_empleado, requerir_roles_empresa
from utils.jwt_helper import requerir_auth
from websockets import emit_reserva_actualizada

reservas_bp = Blueprint("reservas_empresa", __name__, url_prefix="/reservas")


# ============================================
# ENDPOINTS
# ============================================


@reservas_bp.route("/stats/periodos", methods=["GET"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente", "mesero")
def obtener_periodos_reservas(user_id, user_rol, id_local):
    """
    Obtiene los años y meses con reservas registradas, incluyendo conteos.
    Retorna:
    - years: Lista de años con reservas + 1 año adelante, con conteo
    - months: Conteo de reservas por mes para el año seleccionado (si se pasa year)
    """
    from datetime import datetime

    from sqlalchemy import extract, func

    year_param = request.args.get("year")

    db = get_session()
    try:
        # Obtener años únicos con reservas
        years_stmt = (
            select(
                extract("year", Reserva.fecha_reserva).label("year"),
                func.count(Reserva.id).label("count"),
            )
            .where(Reserva.id_local == id_local)
            .group_by(extract("year", Reserva.fecha_reserva))
            .order_by(extract("year", Reserva.fecha_reserva).desc())
        )

        years_result = db.execute(years_stmt).all()

        # Construir lista de años con conteos
        years_data = []
        existing_years = set()

        for row in years_result:
            year_val = int(row.year)
            existing_years.add(year_val)
            years_data.append({"year": year_val, "count": row.count})

        # Agregar el año actual si no existe
        current_year = datetime.now().year
        if current_year not in existing_years:
            years_data.append({"year": current_year, "count": 0})
            existing_years.add(current_year)

        # Agregar 1 año adelante si no existe
        next_year = current_year + 1
        if next_year not in existing_years:
            years_data.append({"year": next_year, "count": 0})

        # Ordenar años de forma descendente
        years_data.sort(key=lambda x: x["year"], reverse=True)

        # Si se solicita un año específico, obtener conteo por mes
        months_data = []
        if year_param:
            try:
                year_int = int(year_param)
                months_stmt = (
                    select(
                        extract("month", Reserva.fecha_reserva).label("month"),
                        func.count(Reserva.id).label("count"),
                    )
                    .where(
                        Reserva.id_local == id_local,
                        extract("year", Reserva.fecha_reserva) == year_int,
                    )
                    .group_by(extract("month", Reserva.fecha_reserva))
                    .order_by(extract("month", Reserva.fecha_reserva))
                )

                months_result = db.execute(months_stmt).all()

                # Crear diccionario de conteos por mes
                month_counts = {int(row.month): row.count for row in months_result}

                # Generar todos los meses (1-12) con sus conteos
                for month_num in range(1, 13):
                    months_data.append(
                        {"month": month_num, "count": month_counts.get(month_num, 0)}
                    )
            except ValueError:
                pass

        return jsonify({"years": years_data, "months": months_data}), 200
    finally:
        db.close()


@reservas_bp.route("/", methods=["GET"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente", "mesero")
def listar_reservas(user_id, user_rol, id_local):
    """Listar todas las reservas del local"""
    fecha_filter = request.args.get("fecha")
    fecha_inicio = request.args.get("fecha_inicio")
    fecha_fin = request.args.get("fecha_fin")
    estado_filter = request.args.get("estado")

    db = get_session()
    try:
        stmt = (
            select(Reserva)
            .options(
                joinedload(Reserva.usuario),
                joinedload(Reserva.reservas_mesa).joinedload(ReservaMesa.mesa),
                joinedload(Reserva.qr_dinamicos),
            )
            .where(Reserva.id_local == id_local)
            .order_by(Reserva.fecha_reserva.desc(), Reserva.hora_reserva.desc())
        )

        # Filtro por fecha exacta o por rango de fechas
        from datetime import datetime

        if fecha_filter:
            try:
                fecha = datetime.strptime(fecha_filter, "%Y-%m-%d").date()
                stmt = stmt.where(Reserva.fecha_reserva == fecha)
            except ValueError:
                pass
        elif fecha_inicio and fecha_fin:
            try:
                f_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
                f_fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
                stmt = stmt.where(
                    Reserva.fecha_reserva >= f_inicio,
                    Reserva.fecha_reserva <= f_fin,
                )
            except ValueError:
                pass

        if estado_filter:
            try:
                estado_enum = EstadoReservaEnum(estado_filter)
                stmt = stmt.where(Reserva.estado == estado_enum)
            except ValueError:
                pass

        reservas = db.execute(stmt).unique().scalars().all()

        result = []
        for reserva in reservas:
            # Obtener mesas asignadas
            mesas = [rm.mesa.nombre for rm in reserva.reservas_mesa if rm.mesa]

            # Obtener codigo QR activo
            qr_codigo = None
            if reserva.qr_dinamicos:
                qr = next((q for q in reserva.qr_dinamicos if q.activo), None)
                if qr:
                    qr_codigo = qr.codigo

            result.append(
                {
                    "id": reserva.id,
                    "usuario_nombre": reserva.usuario.nombre
                    if reserva.usuario
                    else "Usuario",
                    "usuario_telefono": reserva.usuario.telefono
                    if reserva.usuario
                    else None,
                    "fecha": reserva.fecha_reserva.strftime("%Y-%m-%d")
                    if reserva.fecha_reserva
                    else None,
                    "hora": reserva.hora_reserva.strftime("%H:%M")
                    if reserva.hora_reserva
                    else None,
                    "estado": reserva.estado.value if reserva.estado else "pendiente",
                    "mesas": mesas,
                    "codigo_qr": qr_codigo or f"RES-{reserva.id}",
                    "creado_el": reserva.creado_el.isoformat()
                    if reserva.creado_el
                    else None,
                }
            )

        return jsonify(result), 200
    finally:
        db.close()


@reservas_bp.route("/<int:reserva_id>/cancelar", methods=["PATCH"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente", "mesero")
def cancelar_reserva(reserva_id, user_id, user_rol, id_local):
    """Cancelar una reserva"""
    db = get_session()
    try:
        stmt = select(Reserva).where(
            Reserva.id == reserva_id, Reserva.id_local == id_local
        )
        reserva = db.execute(stmt).scalar_one_or_none()

        if not reserva:
            return jsonify({"error": "Reserva no encontrada"}), 404

        if reserva.estado == EstadoReservaEnum.RECHAZADA:
            return jsonify({"error": "La reserva ya fue cancelada"}), 400

        reserva.estado = EstadoReservaEnum.RECHAZADA
        db.commit()

        # Emitir evento WebSocket
        with contextlib.suppress(Exception):
            emit_reserva_actualizada(
                id_local,
                {
                    "id": reserva.id,
                    "estado": reserva.estado.value,
                    "usuario_nombre": reserva.usuario.nombre
                    if reserva.usuario
                    else "Usuario",
                },
            )

        return jsonify(
            {
                "message": "Reserva cancelada exitosamente",
                "reserva": {
                    "id": reserva.id,
                    "estado": reserva.estado.value,
                },
            }
        ), 200
    finally:
        db.close()


@reservas_bp.route("/verificar-qr/<string:codigo>", methods=["GET"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente", "mesero")
def verificar_qr_reserva(codigo, user_id, user_rol, id_local):
    """
    Verifica un código QR de reserva y retorna la información.
    Calcula si la reserva puede ser confirmada (ventana de ±15 minutos).
    """
    from datetime import datetime

    from config import get_logger

    logger = get_logger(__name__)
    logger.info(
        f"[VERIFICAR QR] Código: {codigo} | Local: {id_local} | Usuario: {user_id}"
    )

    db = get_session()
    try:
        # Buscar el QR en la base de datos
        from models.models import QRDinamico

        stmt = (
            select(QRDinamico)
            .options(
                joinedload(QRDinamico.reserva).joinedload(Reserva.usuario),
                joinedload(QRDinamico.reserva)
                .joinedload(Reserva.reservas_mesa)
                .joinedload(ReservaMesa.mesa),
            )
            .where(QRDinamico.codigo == codigo, QRDinamico.activo)
        )

        qr = db.execute(stmt).unique().scalar_one_or_none()

        if not qr:
            logger.warning(f"[VERIFICAR QR] QR no encontrado o inactivo: {codigo}")
            return jsonify({"error": "Código QR inválido o expirado"}), 404

        # Verificar expiración y marcar como inactivo si expiró
        if qr.expiracion and qr.expiracion < datetime.now():
            logger.warning(f"[VERIFICAR QR] QR expirado: {codigo}")
            qr.activo = False
            db.commit()
            return jsonify({"error": "Código QR expirado"}), 400

        if not qr.reserva:
            logger.error(f"[VERIFICAR QR] QR sin reserva asociada: {codigo}")
            return jsonify({"error": "No se encontró una reserva asociada"}), 404

        reserva = qr.reserva
        logger.info(
            f"[VERIFICAR QR] Reserva encontrada - ID: {reserva.id} | Usuario: {reserva.usuario.nombre if reserva.usuario else 'N/A'} | Fecha: {reserva.fecha_reserva} | Hora: {reserva.hora_reserva} | Personas: {reserva.num_personas}"
        )

        # Verificar que la reserva pertenece al local del empleado
        if reserva.id_local != id_local:
            logger.warning(
                f"[VERIFICAR QR] Reserva {reserva.id} no pertenece al local {id_local}"
            )
            return jsonify({"error": "Esta reserva no pertenece a tu local"}), 403

        # Calcular si está en la ventana de confirmación (15 min antes - 15 min después)
        ahora = datetime.now()
        fecha_hora_reserva = datetime.combine(
            reserva.fecha_reserva, reserva.hora_reserva
        )

        diferencia_minutos = (fecha_hora_reserva - ahora).total_seconds() / 60

        # Puede confirmar si está entre -15 y +15 minutos
        puede_confirmar = -15 <= diferencia_minutos <= 15

        # Determinar estado de la ventana
        if diferencia_minutos > 15:
            ventana_estado = "temprano"  # Más de 15 min antes
        elif diferencia_minutos < -15:
            ventana_estado = "tarde"  # Más de 15 min después
        else:
            ventana_estado = "activa"  # En ventana de confirmación

        # Obtener mesas asignadas
        mesas = [rm.mesa.nombre for rm in reserva.reservas_mesa if rm.mesa]

        # Obtener número de personas de la reserva
        num_personas = reserva.num_personas or 1

        return jsonify(
            {
                "success": True,
                "reserva": {
                    "id": reserva.id,
                    "usuario_id": reserva.id_usuario,
                    "usuario_nombre": reserva.usuario.nombre
                    if reserva.usuario
                    else "Usuario",
                    "usuario_telefono": reserva.usuario.telefono
                    if reserva.usuario
                    else None,
                    "fecha_reserva": reserva.fecha_reserva.strftime("%d-%m-%Y"),
                    "hora_reserva": reserva.hora_reserva.strftime("%H:%M"),
                    "num_personas": num_personas,
                    "estado": reserva.estado.value,
                    "mesas": mesas,
                    "codigo_qr": codigo,
                    "puede_confirmar": puede_confirmar,
                    "ventana_estado": ventana_estado,
                    "minutos_hasta_reserva": int(diferencia_minutos),
                },
            }
        ), 200
    finally:
        db.close()


@reservas_bp.route("/<int:reserva_id>/confirmar", methods=["POST"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente", "mesero")
def confirmar_reserva(reserva_id, user_id, user_rol, id_local):
    """
    Confirma una reserva y crea automáticamente un pedido asociado.
    Solo puede confirmarse en la ventana de ±15 minutos.
    """
    from datetime import datetime

    from models.models import Pedido

    db = get_session()
    try:
        # Obtener la reserva
        stmt = (
            select(Reserva)
            .options(
                joinedload(Reserva.usuario),
                joinedload(Reserva.reservas_mesa).joinedload(ReservaMesa.mesa),
                joinedload(Reserva.qr_dinamicos),
            )
            .where(Reserva.id == reserva_id, Reserva.id_local == id_local)
        )
        reserva = db.execute(stmt).unique().scalar_one_or_none()

        if not reserva:
            return jsonify({"error": "Reserva no encontrada"}), 404

        # Verificar que está en estado pendiente
        if reserva.estado != EstadoReservaEnum.PENDIENTE:
            return jsonify({"error": f"La reserva ya fue {reserva.estado.value}"}), 400

        # Verificar ventana de tiempo (±15 minutos)
        ahora = datetime.now()
        fecha_hora_reserva = datetime.combine(
            reserva.fecha_reserva, reserva.hora_reserva
        )
        diferencia_minutos = (fecha_hora_reserva - ahora).total_seconds() / 60

        if not (-15 <= diferencia_minutos <= 15):
            return jsonify(
                {
                    "error": "La reserva solo puede confirmarse entre 15 minutos antes y 15 minutos después de la hora reservada"
                }
            ), 400

        # Obtener la primera mesa asignada
        if not reserva.reservas_mesa:
            return jsonify({"error": "La reserva no tiene mesa asignada"}), 400

        mesa_principal = reserva.reservas_mesa[0].mesa

        # Obtener el QR activo de la reserva
        qr_reserva = next((q for q in reserva.qr_dinamicos if q.activo), None)
        if not qr_reserva:
            return jsonify({"error": "No se encontró QR activo para esta reserva"}), 404

        # Cambiar estado de la reserva a CONFIRMADA
        reserva.estado = EstadoReservaEnum.CONFIRMADA

        # Crear el pedido automáticamente
        from models.models import EstadoPedidoEnum

        # CASO 1 - RESERVA: Copiar num_personas de la Reserva al Pedido
        nuevo_pedido = Pedido(
            id_local=id_local,
            id_mesa=mesa_principal.id,
            id_usuario=reserva.id_usuario,
            id_qr=qr_reserva.id,
            creado_por=user_id,  # El empleado que confirma
            estado=EstadoPedidoEnum.INICIADO,
            total=0,  # Se actualizará cuando agreguen items
            num_personas=reserva.num_personas,  # Copiar de la Reserva
        )

        db.add(nuevo_pedido)
        db.flush()  # Para obtener el ID del pedido

        # Actualizar el QR para asociarlo al pedido
        qr_reserva.id_pedido = nuevo_pedido.id

        # Actualizar estado de la mesa a OCUPADA
        from models.models import EstadoMesaEnum

        mesa_principal.estado = EstadoMesaEnum.OCUPADA

        db.commit()
        db.refresh(nuevo_pedido)

        # Emitir eventos WebSocket
        with contextlib.suppress(Exception):
            emit_reserva_actualizada(
                id_local,
                {
                    "id": reserva.id,
                    "estado": reserva.estado.value,
                    "usuario_nombre": reserva.usuario.nombre
                    if reserva.usuario
                    else "Usuario",
                },
            )

        return jsonify(
            {
                "success": True,
                "message": "Reserva confirmada y pedido creado exitosamente",
                "reserva": {
                    "id": reserva.id,
                    "estado": reserva.estado.value,
                },
                "pedido": {
                    "id": nuevo_pedido.id,
                    "mesa_id": mesa_principal.id,
                    "mesa_nombre": mesa_principal.nombre,
                    "estado": nuevo_pedido.estado.value,
                },
            }
        ), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Error al confirmar reserva: {e!s}"}), 500
    finally:
        db.close()
