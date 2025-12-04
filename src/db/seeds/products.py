import logging

from models import EstadoProductoEnum, Foto, Producto

logger = logging.getLogger(__name__)


def create_products(db):
    # ============ Productos ============
    logger.info("  → Insertando Productos de ejemplo...")
    if db.query(Producto).count() == 0:
        # Productos para Local 1 (Restaurante)
        db.add_all(
            [
                Producto(
                    id_local=1,
                    id_categoria=1,
                    nombre="Empanadas de Pino",
                    descripcion="3 empanadas tradicionales",
                    estado=EstadoProductoEnum.DISPONIBLE,
                    precio=4500,
                ),
                Producto(
                    id_local=1,
                    id_categoria=2,
                    nombre="Lomo a lo Pobre",
                    descripcion="Con papas fritas y huevos",
                    estado=EstadoProductoEnum.DISPONIBLE,
                    precio=9500,
                ),
                Producto(
                    id_local=1,
                    id_categoria=2,
                    nombre="Pastel de Choclo",
                    descripcion="Tradicional chileno",
                    estado=EstadoProductoEnum.DISPONIBLE,
                    precio=7800,
                ),
                Producto(
                    id_local=1,
                    id_categoria=3,
                    nombre="Leche Asada",
                    descripcion="Postre tradicional",
                    estado=EstadoProductoEnum.DISPONIBLE,
                    precio=3200,
                ),
                Producto(
                    id_local=1,
                    id_categoria=4,
                    nombre="Pisco Sour",
                    descripcion="Coctel nacional",
                    estado=EstadoProductoEnum.DISPONIBLE,
                    precio=4500,
                ),
            ]
        )
        # Productos para Local 2 (Bar)
        db.add_all(
            [
                Producto(
                    id_local=2,
                    id_categoria=5,
                    nombre="Cerveza Kunstmann",
                    descripcion="500ml",
                    estado=EstadoProductoEnum.DISPONIBLE,
                    precio=3500,
                ),
                Producto(
                    id_local=2,
                    id_categoria=7,
                    nombre="Mojito",
                    descripcion="Ron, menta, lima",
                    estado=EstadoProductoEnum.DISPONIBLE,
                    precio=5500,
                ),
                Producto(
                    id_local=2,
                    id_categoria=1,
                    nombre="Tabla de Quesos",
                    descripcion="Seleccion de quesos nacionales",
                    estado=EstadoProductoEnum.DISPONIBLE,
                    precio=8900,
                ),
            ]
        )
        # Productos para Local 3 (Cafeteria)
        db.add_all(
            [
                Producto(
                    id_local=3,
                    id_categoria=8,
                    nombre="Café Americano",
                    descripcion="Grande",
                    estado=EstadoProductoEnum.DISPONIBLE,
                    precio=2500,
                ),
                Producto(
                    id_local=3,
                    id_categoria=8,
                    nombre="Cappuccino",
                    descripcion="Grande",
                    estado=EstadoProductoEnum.DISPONIBLE,
                    precio=3200,
                ),
                Producto(
                    id_local=3,
                    id_categoria=3,
                    nombre="Brownie de Chocolate",
                    descripcion="Con helado",
                    estado=EstadoProductoEnum.DISPONIBLE,
                    precio=3800,
                ),
            ]
        )
        db.commit()
        logger.info("    ✓ Productos insertados")

        # Fotos de Productos
        logger.info("  → Insertando Fotos de Productos...")

        # Generamos fotos para todos los productos insertados (IDs 1 al 11)
        fotos_productos = []
        for i in range(1, 12):
            fotos_productos.append(
                Foto(
                    id_producto=i,
                    id_tipo_foto=2,
                    ruta=f"https://picsum.photos/seed/prod{i}/400/400",
                )
            )

        db.add_all(fotos_productos)
        db.commit()
        logger.info(f"    ✓ {len(fotos_productos)} Fotos de Productos insertadas")

    else:
        logger.info("    Productos ya existen")
