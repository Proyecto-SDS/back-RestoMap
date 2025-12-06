from config import get_logger
from models import Usuario

logger = get_logger(__name__)


def create_users(db):
    logger.info("  → Insertando Usuarios de ejemplo...")
    if db.query(Usuario).count() > 0:
        logger.info("    Usuarios ya existen, saltando...")
        return

    # Hash para password: test123
    password_hash = "$2b$12$q6myteznSC8775D4zt/e6OnPZVMv4jxV9ejhmMRpubGnVA1lecciO"
    db.add_all(
        [
            Usuario(
                id_rol=1,
                nombre="Diego Admin",
                correo="admin@test.cl",
                contrasena=password_hash,
                telefono="912345678",
            ),
            Usuario(
                id_rol=None,  # Usuario sin rol = cliente implicito
                nombre="Juan Perez",
                correo="juan@test.cl",
                contrasena=password_hash,
                telefono="987654321",
            ),
            Usuario(
                id_rol=None,  # Usuario sin rol = cliente implicito
                nombre="Maria Gonzalez",
                correo="maria@test.cl",
                contrasena=password_hash,
                telefono="955556666",
            ),
            Usuario(
                id_rol=4,
                id_local=1,
                nombre="Carlos Mesero",
                correo="mesero@test.cl",
                contrasena=password_hash,
                telefono="944443333",
            ),
            Usuario(
                id_rol=3,
                id_local=1,
                nombre="Ana Cocinera",
                correo="cocinero@test.cl",
                contrasena=password_hash,
                telefono="933332222",
            ),
            Usuario(
                id_rol=5,
                id_local=1,
                nombre="Luis Bartender",
                correo="bartender@test.cl",
                contrasena=password_hash,
                telefono="922221111",
            ),
            Usuario(
                id_rol=2,
                id_local=1,
                nombre="Gabriela Gerente",
                correo="gerente@test.cl",
                contrasena=password_hash,
                telefono="911110000",
            ),
        ]
    )
    db.commit()
    logger.info("    ✓ Usuarios insertados (password: test123)")
