from config import get_logger

logger = get_logger(__name__)


def create_qrs(db):
    """
    NO creamos QRs en seeds.
    Los QRs dinámicos se generan en tiempo real mediante endpoints:
    - Para reservas: cuando se confirma una reserva
    - Para mesas: mediante /api/empresa/mesas/<mesa_id>/qr
    """
    logger.info("  → QR Dinamicos: Se generan en tiempo real (no en seeds)")
