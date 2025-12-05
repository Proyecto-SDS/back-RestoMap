"""
Rutas de opiniones
Endpoints: /api/opiniones/*
"""

import traceback
from datetime import datetime

from flask import Blueprint, jsonify
from sqlalchemy.orm import joinedload

from config import get_logger
from database import db_session
from models import Local, Opinion, Usuario
from schemas import OpinionCreateSchema
from utils.jwt_helper import requerir_auth_persona
from utils.validation import validate_json

logger = get_logger(__name__)

opiniones_bp = Blueprint("opiniones", __name__, url_prefix="/api/opiniones")


@opiniones_bp.route("/", methods=["POST"])
@requerir_auth_persona
@validate_json(OpinionCreateSchema)
def crear_opinion(data: OpinionCreateSchema, user_id):
    """
    Crear nueva opinion para un local

    Headers:
        Authorization: Bearer {token}

    Body:
        {
            "localId": 1,
            "puntuacion": 4.5,
            "comentario": "Excelente comida y servicio"
        }

    Response 201:
        {
            "success": true,
            "message": "Opinion creada exitosamente",
            "opinion": {
                "id": 1,
                "localId": "1",
                "usuario": "Juan Perez",
                "puntuacion": 4.5,
                "comentario": "Excelente comida...",
                "fecha": "2024-11-24T12:00:00"
            }
        }

    Response 400:
        {"error": "Datos invalidos", "details": [...]}
        {"error": "Ya tienes una opinion para este local"}

    Response 404:
        {"error": "Local no encontrado"}
    """
    try:
        local_id = data.local_id
        puntuacion = data.puntuacion
        comentario = data.comentario.strip()

        # Verificar que el local existe
        local = db_session.query(Local).filter(Local.id == local_id).first()
        if not local:
            return jsonify({"error": "Local no encontrado"}), 404

        # Verificar que el usuario no tenga ya una opinion para este local
        opinion_existente = (
            db_session.query(Opinion)
            .filter(
                Opinion.id_usuario == user_id,
                Opinion.id_local == local_id,
                Opinion.eliminado_el.is_(None),
            )
            .first()
        )

        if opinion_existente:
            return jsonify({"error": "Ya tienes una opinion para este local"}), 400

        # Crear nueva opinion
        nueva_opinion = Opinion(
            id_usuario=user_id,
            id_local=local_id,
            puntuacion=puntuacion,
            comentario=comentario,
            creado_el=datetime.utcnow(),
        )

        db_session.add(nueva_opinion)
        db_session.commit()
        db_session.refresh(nueva_opinion)

        # Obtener usuario para respuesta
        usuario = db_session.query(Usuario).filter(Usuario.id == user_id).first()
        usuario_nombre = usuario.nombre if usuario else "Usuario"

        return jsonify(
            {
                "success": True,
                "message": "Opinion creada exitosamente",
                "opinion": {
                    "id": nueva_opinion.id,
                    "localId": str(local_id),
                    "usuario": usuario_nombre,
                    # pyrefly: ignore [bad-argument-type]
                    "puntuacion": float(nueva_opinion.puntuacion),
                    "comentario": nueva_opinion.comentario,
                    "fecha": nueva_opinion.creado_el.isoformat(),
                },
            }
        ), 201

    except Exception:
        db_session.rollback()
        traceback.print_exc()
        return jsonify({"error": "Error al crear la opinion"}), 500


@opiniones_bp.route("/mis-opiniones", methods=["GET"])
@requerir_auth_persona
def obtener_mis_opiniones(user_id):
    """
    Obtener todas las opiniones del usuario autenticado

    Headers:
        Authorization: Bearer {token}

    Response 200:
        {
            "opiniones": [
                {
                    "id": 1,
                    "localId": "1",
                    "localNombre": "El Gran Sabor",
                    "puntuacion": 4.5,
                    "comentario": "Excelente comida...",
                    "fecha": "2024-11-24T12:00:00"
                }
            ]
        }
    """
    try:
        opiniones = (
            db_session.query(Opinion)
            # pyrefly: ignore  # bad-argument-type
            .options(joinedload(Opinion.local))
            .filter(Opinion.id_usuario == user_id, Opinion.eliminado_el.is_(None))
            .order_by(Opinion.creado_el.desc())
            .all()
        )

        opiniones_lista = []
        for opinion in opiniones:
            opiniones_lista.append(
                {
                    "id": opinion.id,
                    "localId": str(opinion.id_local),
                    "localNombre": opinion.local.nombre if opinion.local else "Local",
                    # pyrefly: ignore [bad-argument-type]
                    "puntuacion": float(opinion.puntuacion),
                    "comentario": opinion.comentario,
                    "fecha": opinion.creado_el.isoformat()
                    if opinion.creado_el
                    else None,
                }
            )

        return jsonify({"opiniones": opiniones_lista}), 200

    except Exception:
        traceback.print_exc()
        return jsonify({"error": "Error al obtener las opiniones"}), 500


@opiniones_bp.route("/<int:local_id>/user", methods=["GET"])
@requerir_auth_persona
def obtener_opinion_usuario(local_id, user_id):
    """
    Obtener la opinion del usuario autenticado para un local especifico

    Headers:
        Authorization: Bearer {token}

    Response 200:
        {
            "id": 1,
            "localId": "1",
            "usuario": "Juan Perez",
            "puntuacion": 4.5,
            "comentario": "Excelente comida...",
            "fecha": "2024-11-24T12:00:00"
        }

    Response 404:
        {"error": "No tienes opinion para este local"}
    """
    try:
        opinion = (
            db_session.query(Opinion)
            # pyrefly: ignore  # bad-argument-type
            .options(joinedload(Opinion.usuario))
            .filter(
                Opinion.id_usuario == user_id,
                Opinion.id_local == local_id,
                Opinion.eliminado_el.is_(None),
            )
            .first()
        )

        if not opinion:
            return jsonify({"error": "No tienes opinion para este local"}), 404

        return jsonify(
            {
                "id": opinion.id,
                "localId": str(local_id),
                "usuario": opinion.usuario.nombre if opinion.usuario else "Usuario",
                # pyrefly: ignore [bad-argument-type]
                "puntuacion": float(opinion.puntuacion),
                "comentario": opinion.comentario,
                "fecha": opinion.creado_el.isoformat() if opinion.creado_el else None,
            }
        ), 200

    except Exception:
        traceback.print_exc()
        return jsonify({"error": "Error al obtener la opinion"}), 500
