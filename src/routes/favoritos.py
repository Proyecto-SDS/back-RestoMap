"""
Rutas de favoritos
Endpoints: /api/favoritos/*
"""

import logging

from flask import Blueprint, jsonify, request
from sqlalchemy import select

from database import SessionLocal
from models.models import Favorito, Local
from utils.jwt_helper import requerir_auth

logger = logging.getLogger(__name__)

favoritos_bp = Blueprint("favoritos", __name__, url_prefix="/api/favoritos")


def get_db():
    """Obtener sesion de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@favoritos_bp.route("/", methods=["GET"])
@requerir_auth
def get_favoritos(user_id, _user_rol):
    """
    Obtener lista de favoritos del usuario autenticado

    Headers:
        Authorization: Bearer {token}

    Response 200:
        {
            "success": true,
            "favoritos": [
                {
                    "id": "1",
                    "localId": "5",
                    "agregadoEl": "2024-01-01T12:00:00"
                }
            ]
        }
    """
    try:
        db = next(get_db())

        # Obtener favoritos del usuario
        favoritos = (
            db.execute(
                select(Favorito)
                .where(Favorito.id_usuario == user_id)
                .order_by(Favorito.agregado_el.desc())
            )
            .scalars()
            .all()
        )

        return jsonify(
            {
                "success": True,
                "favoritos": [
                    {
                        "id": str(fav.id),
                        "localId": str(fav.id_local),
                        "agregadoEl": fav.agregado_el.isoformat()
                        if fav.agregado_el
                        else None,
                    }
                    for fav in favoritos
                ],
            }
        ), 200

    except Exception as e:
        logger.error(f"Error en get_favoritos: {e!s}")
        return jsonify({"error": "Error al obtener favoritos"}), 500


@favoritos_bp.route("/", methods=["POST"])
@requerir_auth
def add_favorito(user_id, _user_rol):
    """
    Agregar un local a favoritos

    Headers:
        Authorization: Bearer {token}

    Body:
        {
            "localId": "5"
        }

    Response 201:
        {
            "success": true,
            "message": "Local agregado a favoritos",
            "favorito": {
                "id": "1",
                "localId": "5",
                "agregadoEl": "2024-01-01T12:00:00"
            }
        }

    Response 400:
        {"error": "localId es requerido"}
        {"error": "Local no encontrado"}
        {"error": "Este local ya esta en favoritos"}
    """
    try:
        data = request.get_json()

        local_id = data.get("localId")

        if not local_id:
            return jsonify({"error": "localId es requerido"}), 400

        try:
            local_id = int(local_id)
        except (ValueError, TypeError):
            return jsonify({"error": "localId debe ser un número valido"}), 400

        db = next(get_db())

        # Verificar que el local existe
        local = db.execute(
            select(Local).where(Local.id == local_id)
        ).scalar_one_or_none()

        if not local:
            return jsonify({"error": "Local no encontrado"}), 400

        # Verificar si ya existe en favoritos
        favorito_existente = db.execute(
            select(Favorito)
            .where(Favorito.id_usuario == user_id)
            .where(Favorito.id_local == local_id)
        ).scalar_one_or_none()

        if favorito_existente:
            return jsonify({"error": "Este local ya esta en favoritos"}), 400

        # Crear nuevo favorito
        nuevo_favorito = Favorito(id_usuario=user_id, id_local=local_id)

        db.add(nuevo_favorito)
        db.commit()
        db.refresh(nuevo_favorito)

        return jsonify(
            {
                "success": True,
                "message": "Local agregado a favoritos",
                "favorito": {
                    "id": str(nuevo_favorito.id),
                    "localId": str(nuevo_favorito.id_local),
                    "agregadoEl": nuevo_favorito.agregado_el.isoformat()
                    if nuevo_favorito.agregado_el
                    else None,
                },
            }
        ), 201

    except Exception as e:
        logger.error(f"Error en add_favorito: {e!s}")
        return jsonify({"error": "Error al agregar favorito"}), 500


@favoritos_bp.route("/<int:local_id>", methods=["DELETE"])
@requerir_auth
def remove_favorito(user_id, _user_rol, local_id):
    """
    Quitar un local de favoritos

    Headers:
        Authorization: Bearer {token}

    URL Params:
        local_id: ID del local

    Response 200:
        {
            "success": true,
            "message": "Local quitado de favoritos"
        }

    Response 404:
        {"error": "Favorito no encontrado"}
    """
    try:
        db = next(get_db())

        # Buscar favorito
        favorito = db.execute(
            select(Favorito)
            .where(Favorito.id_usuario == user_id)
            .where(Favorito.id_local == local_id)
        ).scalar_one_or_none()

        if not favorito:
            return jsonify({"error": "Favorito no encontrado"}), 404

        db.delete(favorito)
        db.commit()

        return jsonify({"success": True, "message": "Local quitado de favoritos"}), 200

    except Exception as e:
        logger.error(f"Error en remove_favorito: {e!s}")
        return jsonify({"error": "Error al quitar favorito"}), 500


@favoritos_bp.route("/check/<int:local_id>", methods=["GET"])
@requerir_auth
def check_favorito(user_id, _user_rol, local_id):
    """
    Verificar si un local es favorito

    Headers:
        Authorization: Bearer {token}

    URL Params:
        local_id: ID del local

    Response 200:
        {
            "isFavorite": true,
            "favoritoId": "1"
        }

        {
            "isFavorite": false
        }
    """
    try:
        db = next(get_db())

        # Buscar favorito
        favorito = db.execute(
            select(Favorito)
            .where(Favorito.id_usuario == user_id)
            .where(Favorito.id_local == local_id)
        ).scalar_one_or_none()

        if favorito:
            return jsonify({"isFavorite": True, "favoritoId": str(favorito.id)}), 200
        else:
            return jsonify({"isFavorite": False}), 200

    except Exception as e:
        logger.error(f"Error en check_favorito: {e!s}")
        return jsonify({"error": "Error al verificar favorito"}), 500
