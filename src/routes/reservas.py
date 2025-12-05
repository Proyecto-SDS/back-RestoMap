"""
Rutas de reservas
Endpoints: /api/reservas/*
"""

import json
import logging
import traceback
from datetime import date, datetime, timedelta

from flask import Blueprint, jsonify, request
from sqlalchemy.orm import joinedload

from database import db_session
from models import (
    Local,
    Mesa,
    Reserva,
    ReservaMesa,
)
from models.models import EstadoReservaEnum
from services.qr_service import crear_qr_reserva, generar_qr_imagen
from utils.jwt_helper import requerir_auth_persona

reservas_bp = Blueprint("reservas", __name__, url_prefix="/api/reservas")


@reservas_bp.route("/", methods=["POST"])
@requerir_auth_persona
def crear_reserva(user_id):
    """
    Crear nueva reserva para un local

    Headers:
        Authorization: Bearer {token}

    Body:
        {
            "localId": "1",
            "mesaId": "1",
            "fecha": "2024-11-25",
            "hora": "19:30",
            "numeroPersonas": 4
        }

    Response 201:
        {
            "success": true,
            "message": "Reserva creada exitosamente",
            "reserva": {
                "id": 1,
                "localId": "1",
                "localNombre": "El Gran Sabor",
                "mesaId": "1",
                "mesaNombre": "Mesa 1",
                "fecha": "2024-11-25",
                "hora": "19:30",
                "estado": "pendiente",
                "numeroPersonas": 4
            }
        }

    Response 400:
        {"error": "localId, mesaId, fecha y hora son requeridos"}
        {"error": "Formato de fecha invalido"}
        {"error": "La fecha debe ser futura"}
        {"error": "Mesa no disponible para esta fecha y hora"}

    Response 404:
        {"error": "Local no encontrado"}
        {"error": "Mesa no encontrada"}
    """
    try:
        data = request.get_json()

        local_id = data.get("localId")
        mesa_id = data.get("mesaId")
        fecha_str = data.get("fecha")
        hora_str = data.get("hora")
        numero_personas = data.get("numeroPersonas", 2)

        # Validar campos requeridos
        if not local_id or not mesa_id or not fecha_str or not hora_str:
            return jsonify(
                {"error": "localId, mesaId, fecha y hora son requeridos"}
            ), 400

        # Convertir IDs
        try:
            local_id = int(local_id)
            mesa_id = int(mesa_id)
        except ValueError:
            return jsonify({"error": "localId y mesaId deben ser números"}), 400

        # Parsear fecha
        try:
            fecha_reserva = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Formato de fecha invalido. Use: YYYY-MM-DD"}), 400

        # Parsear hora
        try:
            hora_reserva = datetime.strptime(hora_str, "%H:%M").time()
        except ValueError:
            return jsonify({"error": "Formato de hora invalido. Use: HH:MM"}), 400

        # Validar que la fecha sea futura (o hoy)
        if fecha_reserva < date.today():
            return jsonify({"error": "La fecha debe ser futura"}), 400

        # Verificar que el local existe
        local = db_session.query(Local).filter(Local.id == local_id).first()
        if not local:
            return jsonify({"error": "Local no encontrado"}), 404

        # Verificar que la mesa existe y pertenece al local
        mesa = (
            db_session.query(Mesa)
            .filter(Mesa.id == mesa_id, Mesa.id_local == local_id)
            .first()
        )

        if not mesa:
            return jsonify({"error": "Mesa no encontrada en este local"}), 404

        # Verificar capacidad de la mesa
        if numero_personas > mesa.capacidad:
            return jsonify(
                {
                    "error": f"La mesa seleccionada tiene capacidad para {mesa.capacidad} personas"
                }
            ), 400

        # Verificar que el usuario no tenga ya una reserva activa en este local
        reserva_activa_usuario = (
            db_session.query(Reserva)
            .filter(
                Reserva.id_usuario == user_id,
                Reserva.id_local == local_id,
                Reserva.estado == EstadoReservaEnum.PENDIENTE,
            )
            .first()
        )

        if reserva_activa_usuario:
            return jsonify(
                {
                    "error": "Ya tienes una reserva pendiente en este restaurante. Debes cancelarla antes de crear una nueva."
                }
            ), 400

        # Verificar disponibilidad de la mesa para esa fecha y hora
        # Considerar un rango de ±75 minutos (1 hora y 15 minutos)
        hora_inicio = (
            datetime.combine(date.today(), hora_reserva) - timedelta(minutes=75)
        ).time()
        hora_fin = (
            datetime.combine(date.today(), hora_reserva) + timedelta(minutes=75)
        ).time()

        reservas_existentes = (
            db_session.query(Reserva)
            .join(ReservaMesa)
            .filter(
                ReservaMesa.id_mesa == mesa_id,
                Reserva.fecha_reserva == fecha_reserva,
                Reserva.hora_reserva >= hora_inicio,
                Reserva.hora_reserva <= hora_fin,
                Reserva.estado.in_(["pendiente", "confirmada"]),
            )
            .first()
        )

        if reservas_existentes:
            return jsonify(
                {
                    "error": "Mesa no disponible para esta fecha y hora. Por favor elija otro horario."
                }
            ), 400

        # Crear nueva reserva
        nueva_reserva = Reserva(
            id_local=local_id,
            id_usuario=user_id,
            fecha_reserva=fecha_reserva,
            hora_reserva=hora_reserva,
            estado=EstadoReservaEnum.PENDIENTE,
            creado_el=datetime.utcnow(),
        )

        db_session.add(nueva_reserva)
        db_session.flush()  # Para obtener el ID

        # Crear relacion reserva-mesa (sin prioridad, se calcula dinámicamente)
        reserva_mesa = ReservaMesa(
            id_reserva=nueva_reserva.id,
            id_mesa=mesa_id,
        )

        db_session.add(reserva_mesa)
        db_session.commit()

        # Generar QR dinamico para la reserva
        logger = logging.getLogger(__name__)

        try:
            logger.info(
                f"[DEBUG] Generando QR para reserva {nueva_reserva.id}, mesa {mesa_id}"
            )
            codigo_qr, qr_base64 = crear_qr_reserva(
                # pyrefly: ignore [bad-argument-type]
                id_reserva=nueva_reserva.id,
                id_mesa=mesa_id,
                id_usuario=user_id,
                minutos_tolerancia=10,  # Expira 10 minutos después de la hora de reserva
            )
            logger.info(f"[DEBUG] QR generado exitosamente. Codigo: {codigo_qr}")
            logger.info(
                f"[DEBUG] QR base64 length: {len(qr_base64) if qr_base64 else 0}"
            )
        except Exception as e:
            logger.error(f"[ERROR] Fallo al generar QR: {e!s}")
            logger.error(traceback.format_exc())
            # Si falla la generacion del QR, no fallar toda la reserva
            codigo_qr = None
            qr_base64 = None

        return jsonify(
            {
                "success": True,
                "message": "Reserva creada exitosamente",
                "reserva": {
                    "id": nueva_reserva.id,
                    "localId": str(local_id),
                    "localNombre": local.nombre,
                    "mesaId": str(mesa_id),
                    "mesaNombre": mesa.nombre,
                    "fecha": fecha_str,
                    "hora": hora_str,
                    "estado": "pendiente",
                    "numeroPersonas": numero_personas,
                    "codigoQR": codigo_qr,
                    "qrImage": qr_base64,
                },
            }
        ), 201

    except Exception:
        db_session.rollback()
        traceback.print_exc()
        return jsonify({"error": "Error al crear la reserva"}), 500


@reservas_bp.route("/mis-reservas", methods=["GET"])
@requerir_auth_persona
def obtener_mis_reservas(user_id):
    """
    Obtener todas las reservas del usuario autenticado

    Headers:
        Authorization: Bearer {token}

    Response 200:
        {
            "reservas": [
                {
                    "id": 1,
                    "localId": "1",
                    "localNombre": "El Gran Sabor",
                    "fecha": "2024-11-25",
                    "hora": "19:30",
                    "estado": "pendiente",
                    "mesas": ["Mesa 1", "Mesa 2"]
                }
            ]
        }
    """
    try:
        reservas = (
            db_session.query(Reserva)
            .options(
                joinedload(Reserva.local).joinedload(Local.direccion),
                joinedload(Reserva.local).joinedload(Local.fotos),
                joinedload(Reserva.local).joinedload(Local.tipo_local),
                joinedload(Reserva.reservas_mesa).joinedload(ReservaMesa.mesa),
                joinedload(Reserva.qr_dinamicos),
            )
            .filter(Reserva.id_usuario == user_id)
            .order_by(Reserva.fecha_reserva.desc(), Reserva.hora_reserva.desc())
            .all()
        )

        reservas_lista = []
        for reserva in reservas:
            mesas_nombres = [rm.mesa.nombre for rm in reserva.reservas_mesa if rm.mesa]

            # Obtener codigo QR activo
            qr_codigo = None
            if reserva.qr_dinamicos:
                # Buscar el QR mas reciente o activo
                qr = next((q for q in reserva.qr_dinamicos if q.activo), None)
                if qr:
                    qr_codigo = qr.codigo

            # Obtener imagen del local (banner o primera foto)
            local_imagen = None
            if reserva.local and reserva.local.fotos:
                # Intentar buscar banner
                banner = next(
                    (f for f in reserva.local.fotos if f.id_tipo_foto == 1), None
                )  # Asumiendo 1 es banner
                local_imagen = banner.ruta if banner else reserva.local.fotos[0].ruta

            # Obtener direccion
            direccion_str = ""
            if reserva.local and reserva.local.direccion:
                d = reserva.local.direccion
                direccion_str = f"{d.calle} {d.numero}"

            # Generar imagen QR si hay codigo
            qr_base64 = None
            if qr_codigo:
                try:
                    qr_data = {
                        "tipo": "reserva",
                        "codigo": qr_codigo,
                        "reserva_id": reserva.id,
                        "mesa_id": reserva.reservas_mesa[0].id_mesa
                        if reserva.reservas_mesa
                        else None,
                        "local_id": reserva.id_local,
                        "fecha": reserva.fecha_reserva.isoformat()
                        if reserva.fecha_reserva
                        else None,
                        "hora": reserva.hora_reserva.strftime("%H:%M")
                        if reserva.hora_reserva
                        else None,
                    }
                    qr_string = json.dumps(qr_data)
                    qr_base64 = generar_qr_imagen(qr_string)
                except Exception as e:
                    print(f"Error generando QR para reserva {reserva.id}: {e}")

            reservas_lista.append(
                {
                    "id": reserva.id,
                    "localId": str(reserva.id_local),
                    "localNombre": reserva.local.nombre if reserva.local else "Local",
                    "localTipo": reserva.local.tipo_local.nombre
                    if reserva.local and reserva.local.tipo_local
                    else "Restaurante",
                    "localImagen": local_imagen,
                    "localDireccion": direccion_str,
                    "fecha": reserva.fecha_reserva.strftime("%Y-%m-%d")
                    if reserva.fecha_reserva
                    else None,
                    "hora": reserva.hora_reserva.strftime("%H:%M")
                    if reserva.hora_reserva
                    else None,
                    "estado": reserva.estado.value if reserva.estado else "pendiente",
                    "mesas": mesas_nombres,
                    "codigoQR": qr_codigo or f"RES-{reserva.id}",
                    "qrImage": qr_base64,
                }
            )

        return jsonify({"reservas": reservas_lista}), 200

    except Exception:
        traceback.print_exc()
        return jsonify({"error": "Error al obtener las reservas"}), 500
