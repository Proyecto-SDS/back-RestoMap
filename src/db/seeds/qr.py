from datetime import datetime, timedelta

from config import get_logger
from models import (
    EstadoReservaEnum,
    QRDinamico,
    Reserva,
    ReservaMesa,
)

logger = get_logger(__name__)


def create_qrs(db):
    # ============ QR Dinamicos ============
    logger.info("  → Insertando QR Dinamicos adicionales de ejemplo...")

    # Los QRs principales ya fueron creados en create_orders
    # Aquí solo creamos QRs adicionales para reservas

    qrs_to_add = []

    # QR para una Reserva Confirmada (si existe y no tiene QR)
    reserva_confirmada = (
        db.query(Reserva).filter(Reserva.estado == EstadoReservaEnum.CONFIRMADA).first()
    )

    if reserva_confirmada:
        # Verificar si ya tiene QR
        qr_existente = (
            db.query(QRDinamico)
            .filter(QRDinamico.id_reserva == reserva_confirmada.id)
            .first()
        )

        if not qr_existente:
            reserva_mesa = (
                db.query(ReservaMesa)
                .filter(ReservaMesa.id_reserva == reserva_confirmada.id)
                .first()
            )

            if reserva_mesa:
                qrs_to_add.append(
                    QRDinamico(
                        id_mesa=reserva_mesa.id_mesa,
                        id_pedido=None,
                        id_reserva=reserva_confirmada.id,
                        id_usuario=reserva_confirmada.id_usuario,
                        codigo=f"QR-R{reserva_confirmada.id}-M{reserva_mesa.id_mesa}-AUTO",
                        expiracion=datetime.now() + timedelta(days=1),
                        activo=True,
                    )
                )

    if qrs_to_add:
        db.add_all(qrs_to_add)
        db.commit()
        logger.info(f"    ✓ {len(qrs_to_add)} QR Dinamicos adicionales insertados")
    else:
        logger.info("    ✓ QRs ya creados en pasos anteriores")
