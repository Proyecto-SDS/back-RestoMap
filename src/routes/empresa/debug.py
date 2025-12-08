"""
Rutas para debug de QRs (solo desarrollo)
Prefix: /api/empresa/debug/*
"""

from flask import Blueprint, jsonify
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from database import get_session
from models.models import QRDinamico
from routes.empresa import requerir_empleado, requerir_roles_empresa
from utils.jwt_helper import requerir_auth

debug_bp = Blueprint("debug", __name__, url_prefix="/debug")


@debug_bp.route("/qrs", methods=["GET"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente", "mesero")
def listar_todos_qrs(user_id, user_rol, id_local):
    """Listar todos los QRs del local para debug"""
    db = get_session()
    try:
        # Obtener QRs de mesas del local
        stmt = (
            select(QRDinamico)
            .options(
                joinedload(QRDinamico.mesa),
                joinedload(QRDinamico.pedido),
                joinedload(QRDinamico.reserva),
            )
            .join(QRDinamico.mesa)
            .where(QRDinamico.mesa.has(id_local=id_local))
            .order_by(QRDinamico.creado_el.desc())
        )
        qrs = db.execute(stmt).unique().scalars().all()

        result = []
        for qr in qrs:
            result.append(
                {
                    "id": qr.id,
                    "codigo": qr.codigo,
                    "activo": qr.activo,
                    "expiracion": qr.expiracion.isoformat() if qr.expiracion else None,
                    "creado_el": qr.creado_el.isoformat() if qr.creado_el else None,
                    "num_personas": qr.num_personas,
                    "id_mesa": qr.id_mesa,
                    "mesa_nombre": qr.mesa.nombre if qr.mesa else None,
                    "id_pedido": qr.id_pedido,
                    "pedido": {
                        "id": qr.pedido.id,
                        "estado": qr.pedido.estado.value
                        if qr.pedido and qr.pedido.estado
                        else None,
                        "total": qr.pedido.total if qr.pedido else None,
                    }
                    if qr.pedido
                    else None,
                    "id_reserva": qr.id_reserva,
                    "id_usuario": qr.id_usuario,
                }
            )

        return jsonify({"total": len(result), "qrs": result}), 200
    finally:
        db.close()


@debug_bp.route("/qrs/<int:mesa_id>", methods=["GET"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente", "mesero")
def listar_qrs_mesa(mesa_id, user_id, user_rol, id_local):
    """Listar todos los QRs de una mesa específica para debug"""
    db = get_session()
    try:
        stmt = (
            select(QRDinamico)
            .options(
                joinedload(QRDinamico.mesa),
                joinedload(QRDinamico.pedido),
            )
            .where(QRDinamico.id_mesa == mesa_id)
            .order_by(QRDinamico.creado_el.desc())
        )
        qrs = db.execute(stmt).unique().scalars().all()

        result = []
        for qr in qrs:
            result.append(
                {
                    "id": qr.id,
                    "codigo": qr.codigo,
                    "activo": qr.activo,
                    "expiracion": qr.expiracion.isoformat() if qr.expiracion else None,
                    "creado_el": qr.creado_el.isoformat() if qr.creado_el else None,
                    "num_personas": qr.num_personas,
                    "id_pedido": qr.id_pedido,
                    "pedido_estado": qr.pedido.estado.value
                    if qr.pedido and qr.pedido.estado
                    else None,
                    "id_reserva": qr.id_reserva,
                }
            )

        return jsonify(
            {
                "mesa_id": mesa_id,
                "total": len(result),
                "activos": len([q for q in result if q["activo"]]),
                "qrs": result,
            }
        ), 200
    finally:
        db.close()


@debug_bp.route("/qrs/limpiar", methods=["POST"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente", "mesero")
def limpiar_qrs_huerfanos(user_id, user_rol, id_local):
    """
    Desactiva QRs que tienen pedidos cancelados/completados pero siguen activos.
    Esto es un endpoint de limpieza/sincronización para corregir inconsistencias.
    """
    from models.models import EstadoPedidoEnum

    db = get_session()
    try:
        # Buscar QRs activos con pedidos cancelados o completados
        stmt = (
            select(QRDinamico)
            .options(joinedload(QRDinamico.pedido), joinedload(QRDinamico.mesa))
            .join(QRDinamico.mesa)
            .where(
                QRDinamico.mesa.has(id_local=id_local),
                QRDinamico.activo.is_(True),
                QRDinamico.id_pedido.isnot(None),
            )
        )
        qrs = db.execute(stmt).unique().scalars().all()

        limpiados = []
        for qr in qrs:
            if qr.pedido and qr.pedido.estado in [
                EstadoPedidoEnum.CANCELADO,
                EstadoPedidoEnum.COMPLETADO,
            ]:
                qr.activo = False
                limpiados.append(
                    {
                        "qr_id": qr.id,
                        "codigo": qr.codigo,
                        "pedido_id": qr.id_pedido,
                        "pedido_estado": qr.pedido.estado.value,
                    }
                )

        db.commit()

        return jsonify(
            {
                "message": f"Se desactivaron {len(limpiados)} QRs huérfanos",
                "qrs_limpiados": limpiados,
            }
        ), 200
    finally:
        db.close()
