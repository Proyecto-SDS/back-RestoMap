import logging
from datetime import date, time, timedelta

from models import EstadoReservaEnum, EstadoReservaMesaEnum, Reserva, ReservaMesa

logger = logging.getLogger(__name__)


def create_reservations(db):
    # ============ Reservas ============
    logger.info("  → Insertando Reservas de ejemplo...")
    if db.query(Reserva).count() == 0:
        # Reserva confirmada
        reserva1 = Reserva(
            id_local=1,
            id_usuario=2,
            fecha_reserva=date.today() + timedelta(days=2),
            hora_reserva=time(20, 0),
            estado=EstadoReservaEnum.CONFIRMADA,
        )
        # Reserva pendiente
        reserva2 = Reserva(
            id_local=2,
            id_usuario=3,
            fecha_reserva=date.today() + timedelta(days=5),
            hora_reserva=time(21, 30),
            estado=EstadoReservaEnum.PENDIENTE,
        )
        db.add_all([reserva1, reserva2])
        db.commit()

        # Asignar mesas a reservas
        db.add_all(
            [
                ReservaMesa(
                    id_reserva=reserva1.id,
                    id_mesa=1,
                    prioridad=EstadoReservaMesaEnum.ALTA,
                ),
                ReservaMesa(
                    id_reserva=reserva1.id,
                    id_mesa=2,
                    prioridad=EstadoReservaMesaEnum.MEDIA,
                ),
                ReservaMesa(
                    id_reserva=reserva2.id,
                    id_mesa=6,
                    prioridad=EstadoReservaMesaEnum.ALTA,
                ),
            ]
        )
        db.commit()
        logger.info("    ✓ Reservas insertadas")
    else:
        logger.info("    Reservas ya existen")
