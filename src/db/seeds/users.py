from config import get_logger
from models import Usuario

logger = get_logger(__name__)


def create_users(db):
    logger.info("  → Insertando Usuarios de ejemplo...")
    if db.query(Usuario).count() > 0:
        logger.info("    Usuarios ya existen, saltando...")
        return

    # Hash para password: Test123
    password_hash = "$2b$12$H9bKVr0c/jk3nXAw80hxbeq9R9iGuDfZvf6/uWhcFiH3XvCFrRgRS"
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
            # Gerente Local 1 - El Gran Sabor
            Usuario(
                id_rol=2,
                id_local=1,
                nombre="Gabriela Gerente",
                correo="gerente@test.cl",
                contrasena=password_hash,
                telefono="911110000",
            ),
            # Gerente Local 2 - Bar La Terraza
            Usuario(
                id_rol=2,
                id_local=2,
                nombre="Roberto Gonzalez",
                correo="gerente2@test.cl",
                contrasena=password_hash,
                telefono="911110002",
            ),
            # Gerente Local 3 - Restobar del Parque
            Usuario(
                id_rol=2,
                id_local=3,
                nombre="Patricia Muñoz",
                correo="gerente3@test.cl",
                contrasena=password_hash,
                telefono="911110003",
            ),
            # Gerente Local 4 - Rincon Peruano
            Usuario(
                id_rol=2,
                id_local=4,
                nombre="Fernando Quispe",
                correo="gerente4@test.cl",
                contrasena=password_hash,
                telefono="911110004",
            ),
            # Gerente Local 5 - The Old Pub
            Usuario(
                id_rol=2,
                id_local=5,
                nombre="Michael Brown",
                correo="gerente5@test.cl",
                contrasena=password_hash,
                telefono="911110005",
            ),
        ]
    )
    db.commit()
    logger.info("    ✓ Usuarios insertados (password: Test123)")
