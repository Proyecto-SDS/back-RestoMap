"""
Rutas para gestión de encomiendas (items de cocina/barra)
Prefix: /api/empresa/encomiendas/*
"""

import contextlib

from flask import Blueprint, jsonify, request
from pydantic import BaseModel, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from database import get_session
from models.models import Encomienda, EstadoEncomiendaEnum
from routes.empresa import requerir_empleado, requerir_roles_empresa
from utils.jwt_helper import requerir_auth
from websockets import emit_estado_encomienda

encomiendas_bp = Blueprint("encomiendas", __name__, url_prefix="/encomiendas")


class EncomiendaEstadoSchema(BaseModel):
    estado: EstadoEncomiendaEnum


@encomiendas_bp.route("/<int:encomienda_id>/estado", methods=["PATCH"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente", "mesero", "cocinero", "bartender")
def cambiar_estado_encomienda(encomienda_id, user_id, user_rol, id_local):
    """Cambiar estado de una encomienda"""
    try:
        data = EncomiendaEstadoSchema(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": "Datos inválidos", "details": e.errors()}), 400

    db = get_session()
    try:
        # Buscar encomienda y su pedido asociado para verificar permisos de local
        stmt = (
            select(Encomienda)
            .options(joinedload(Encomienda.pedido))
            .where(Encomienda.id == encomienda_id)
        )
        encomienda = db.execute(stmt).scalar_one_or_none()

        if not encomienda:
            return jsonify({"error": "Encomienda no encontrada"}), 404

        # Verificar que pertenece al local del empleado
        if not encomienda.pedido or encomienda.pedido.id_local != id_local:
            return jsonify({"error": "Acceso denegado a esta encomienda"}), 403

        # Actualizar estado
        encomienda.estado = data.estado
        db.commit()

        # Emitir evento WebSocket
        with contextlib.suppress(Exception):
            emit_estado_encomienda(
                id_local,
                encomienda.pedido.id,
                encomienda.id,
                encomienda.estado.value,
            )

        return jsonify(
            {
                "message": "Estado de encomienda actualizado",
                "encomienda": {
                    "id": encomienda.id,
                    "estado": encomienda.estado.value,
                    "pedido_id": encomienda.pedido.id,
                },
            }
        ), 200
    finally:
        db.close()
