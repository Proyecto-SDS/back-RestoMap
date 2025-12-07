from config import get_logger

logger = get_logger(__name__)


def create_reservations(db):
    """
    NO creamos Reservas en seeds.
    Las reservas se crean en tiempo real mediante endpoints:
    - Cliente: POST /api/cliente/reservas
    - Se confirman desde el dashboard del mesero
    """
    logger.info("  → Reservas: Se crean en tiempo real (no en seeds)")
