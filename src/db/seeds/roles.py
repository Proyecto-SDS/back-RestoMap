import logging

from models import Rol

logger = logging.getLogger(__name__)


def create_roles(db):
    logger.info("  → Insertando Roles...")
    if db.query(Rol).count() > 0:
        logger.info("    Roles ya existen, saltando...")
        return

    db.add_all(
        [
            Rol(nombre="admin"),
            Rol(nombre="gerente"),
            Rol(nombre="chef"),
            Rol(nombre="mesero"),
            Rol(nombre="bartender"),
            Rol(nombre="cliente"),
        ]
    )
    db.commit()
    logger.info("    ✓ Roles insertados")
