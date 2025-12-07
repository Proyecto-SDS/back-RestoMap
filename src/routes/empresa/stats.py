"""
Rutas para estadísticas del local
Prefix: /api/empresa/stats/*
"""

from flask import Blueprint, jsonify
from sqlalchemy import func, select

from database import get_session
from models.models import EstadoPedidoEnum, Mesa, Pedido, Usuario
from routes.empresa import requerir_empleado, requerir_roles_empresa
from utils.jwt_helper import requerir_auth

stats_bp = Blueprint("stats", __name__, url_prefix="/stats")


@stats_bp.route("/dashboard", methods=["GET"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente")
def stats_dashboard(user_id, user_rol, id_local):
    """Obtener estadísticas generales del dashboard del gerente"""
    db = get_session()
    try:
        # Empleados
        empleados_total = (
            db.execute(
                select(func.count())
                .select_from(Usuario)
                .where(Usuario.id_local == id_local)
            ).scalar()
            or 0
        )

        empleados_activos = (
            db.execute(
                select(func.count())
                .select_from(Usuario)
                .where(Usuario.id_local == id_local, Usuario.activo.is_(True))
            ).scalar()
            or 0
        )

        # Mesas
        mesas_total = (
            db.execute(
                select(func.count()).select_from(Mesa).where(Mesa.id_local == id_local)
            ).scalar()
            or 0
        )

        mesas_ocupadas = (
            db.execute(
                select(func.count())
                .select_from(Mesa)
                .where(Mesa.id_local == id_local, Mesa.estado == "ocupada")
            ).scalar()
            or 0
        )

        # Pedidos - Todos los pedidos activos (que no estan completados ni cancelados)
        pedidos_en_proceso = (
            db.execute(
                select(func.count())
                .select_from(Pedido)
                .where(
                    Pedido.id_local == id_local,
                    Pedido.estado.in_(
                        [
                            EstadoPedidoEnum.INICIADO,
                            EstadoPedidoEnum.RECEPCION,
                            EstadoPedidoEnum.EN_PROCESO,
                            EstadoPedidoEnum.TERMINADO,
                            EstadoPedidoEnum.SERVIDO,
                        ]
                    ),
                )
            ).scalar()
            or 0
        )

        return jsonify(
            {
                "empleados_total": empleados_total,
                "empleados_activos": empleados_activos,
                "empleados_inactivos": empleados_total - empleados_activos,
                "mesas_total": mesas_total,
                "mesas_ocupadas": mesas_ocupadas,
                "pedidos_en_proceso": pedidos_en_proceso,
            }
        ), 200
    finally:
        db.close()
