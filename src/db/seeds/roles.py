from config import get_logger
from models import Rol

logger = get_logger(__name__)


def create_roles(db):
    logger.info("  → Insertando Roles...")
    if db.query(Rol).count() > 0:
        logger.info("    Roles ya existen, saltando...")
        return

    db.add_all(
        [
            Rol(nombre="admin"),
            Rol(nombre="gerente"),
            Rol(nombre="cocinero"),
            Rol(nombre="mesero"),
            Rol(nombre="bartender"),
        ]
    )
    db.commit()
    logger.info("    ✓ Roles insertados")
