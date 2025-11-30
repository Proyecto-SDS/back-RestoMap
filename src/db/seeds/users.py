import logging
from models import Usuario

logger = logging.getLogger(__name__)

def create_users(db):
    logger.info("  → Insertando Usuarios de ejemplo...")
    if db.query(Usuario).count() > 0:
        logger.info("    ⚠ Usuarios ya existen, saltando...")
        return

    # Hash para password: test123
    password_hash = "$2b$12$q6myteznSC8775D4zt/e6OnPZVMv4jxV9ejhmMRpubGnVA1lecciO"
    db.add_all([
        # Admin (sin local vinculado)
        Usuario(id_rol=1, nombre="Admin Test", correo="admin@test.cl", 
               contrasena=password_hash, 
               telefono="912345678",
               id_local=None),
        # Clientes (sin local vinculado)
        Usuario(id_rol=6, nombre="Juan Pérez", correo="juan@test.cl", 
               contrasena=password_hash, 
               telefono="987654321",
               id_local=None),
        Usuario(id_rol=6, nombre="María González", correo="maria@test.cl", 
               contrasena=password_hash, 
               telefono="955556666",
               id_local=None),
        # Empleados vinculados a locales
        Usuario(id_rol=2, nombre="Pedro Gerente", correo="gerente@test.cl", 
               contrasena=password_hash, 
               telefono="911112222",
               id_local=1),  # El Gran Sabor
        Usuario(id_rol=3, nombre="Ana Chef", correo="chef@test.cl", 
               contrasena=password_hash, 
               telefono="933332222",
               id_local=1),  # El Gran Sabor
        Usuario(id_rol=4, nombre="Carlos Mesero", correo="mesero@test.cl", 
               contrasena=password_hash, 
               telefono="944443333",
               id_local=2),  # Bar La Terraza
        Usuario(id_rol=5, nombre="Luis Bartender", correo="bartender@test.cl", 
               contrasena=password_hash, 
               telefono="922223333",
               id_local=2),  # Bar La Terraza
    ])
    db.commit()
    logger.info("    ✓ Usuarios insertados (password: test123)")
    logger.info("    ℹ Empleados vinculados: Gerente y Chef → Local 1, Mesero y Bartender → Local 2")
