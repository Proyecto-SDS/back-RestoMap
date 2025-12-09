"""
Rutas para información del local de empresa
Prefix: /api/empresa/local/*
"""

from flask import Blueprint, jsonify, request
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from database import get_session
from models import Direccion, Local
from utils.jwt_helper import verificar_token

local_bp = Blueprint("local", __name__, url_prefix="/local")


@local_bp.route("/", methods=["GET"])
def obtener_local_info():
    """Obtiene la información del local del empleado autenticado."""
    # Obtener usuario del token
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Token no proporcionado"}), 401

    token = auth_header.split(" ")[1]
    payload = verificar_token(token)
    if not payload:
        return jsonify({"error": "Token inválido"}), 401

    id_local = payload.get("id_local")
    if not id_local:
        return jsonify({"error": "Usuario no asociado a un local"}), 403

    db = get_session()
    try:
        stmt = (
            select(Local)
            .options(
                joinedload(Local.direccion).joinedload(Direccion.comuna),
                joinedload(Local.tipo_local),
                joinedload(Local.horarios),
                joinedload(Local.redes),
            )
            .where(Local.id == id_local)
        )
        local = db.execute(stmt).unique().scalar_one_or_none()

        if not local:
            return jsonify({"error": "Local no encontrado"}), 404

        # Formatear horarios
        horarios = []
        for h in local.horarios:
            horarios.append(
                {
                    "dia_semana": h.dia_semana,
                    "hora_apertura": h.hora_apertura.strftime("%H:%M")
                    if h.hora_apertura
                    else None,
                    "hora_cierre": h.hora_cierre.strftime("%H:%M")
                    if h.hora_cierre
                    else None,
                    "abierto": h.abierto,
                }
            )

        # Formatear redes
        redes = []
        for r in local.redes:
            redes.append(
                {
                    "id_tipo_red": r.id_tipo_red,
                    "url": r.url,
                }
            )

        return jsonify(
            {
                "id": local.id,
                "nombre": local.nombre,
                "descripcion": local.descripcion,
                "telefono": local.telefono,
                "correo": local.correo,
                "tipo_local": local.tipo_local.nombre if local.tipo_local else None,
                "direccion": {
                    "calle": local.direccion.calle if local.direccion else None,
                    "numero": local.direccion.numero if local.direccion else None,
                    "comuna": local.direccion.comuna.nombre
                    if local.direccion and local.direccion.comuna
                    else None,
                }
                if local.direccion
                else None,
                "horarios": horarios,
                "redes": redes,
            }
        ), 200

    finally:
        db.close()
