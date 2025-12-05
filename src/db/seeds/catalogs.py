from config import get_logger
from models import Categoria, Comuna, TipoFoto, TipoLocal, TipoRed

logger = get_logger(__name__)


def create_catalogs(db):
    # ============ Tipos de Local ============
    logger.info("  → Insertando Tipos de Local...")
    if db.query(TipoLocal).count() == 0:
        db.add_all(
            [
                TipoLocal(nombre="Restaurante"),
                TipoLocal(nombre="Bar"),
                TipoLocal(nombre="Restobar"),
            ]
        )
        db.commit()
        logger.info("    ✓ Tipos de Local insertados")
    else:
        logger.info("    Tipos de Local ya existen")

    # ============ Comunas ============
    logger.info("  → Insertando Comunas de Santiago...")
    if db.query(Comuna).count() == 0:
        db.add_all(
            [
                Comuna(nombre="Santiago"),
                Comuna(nombre="Cerrillos"),
                Comuna(nombre="Cerro Navia"),
                Comuna(nombre="Conchali"),
                Comuna(nombre="El Bosque"),
                Comuna(nombre="Estacion Central"),
                Comuna(nombre="Huechuraba"),
                Comuna(nombre="Independencia"),
                Comuna(nombre="La Cisterna"),
                Comuna(nombre="La Florida"),
                Comuna(nombre="La Granja"),
                Comuna(nombre="La Pintana"),
                Comuna(nombre="La Reina"),
                Comuna(nombre="Las Condes"),
                Comuna(nombre="Lo Barnechea"),
                Comuna(nombre="Lo Espejo"),
                Comuna(nombre="Lo Prado"),
                Comuna(nombre="Macul"),
                Comuna(nombre="Maipú"),
                Comuna(nombre="Ñuñoa"),
                Comuna(nombre="Pedro Aguirre Cerda"),
                Comuna(nombre="Peñalolén"),
                Comuna(nombre="Providencia"),
                Comuna(nombre="Pudahuel"),
                Comuna(nombre="Quilicura"),
                Comuna(nombre="Quinta Normal"),
                Comuna(nombre="Recoleta"),
                Comuna(nombre="Renca"),
                Comuna(nombre="San Joaquin"),
                Comuna(nombre="San Miguel"),
                Comuna(nombre="San Ramon"),
                Comuna(nombre="Vitacura"),
            ]
        )
        db.commit()
        logger.info("    ✓ Comunas insertadas")
    else:
        logger.info("    Comunas ya existen")

    # ============ Tipos de Redes Sociales ============
    logger.info("  → Insertando Tipos de Redes Sociales...")
    if db.query(TipoRed).count() == 0:
        db.add_all(
            [
                TipoRed(nombre="Sitio Web"),
                TipoRed(nombre="Instagram"),
                TipoRed(nombre="Facebook"),
                TipoRed(nombre="TikTok"),
                TipoRed(nombre="YouTube"),
                TipoRed(nombre="X/Twitter"),
                TipoRed(nombre="WhatsApp"),
                TipoRed(nombre="LinkedIn"),
            ]
        )
        db.commit()
        logger.info("    ✓ Tipos de Redes Sociales insertados")
    else:
        logger.info("    Tipos de Redes Sociales ya existen")

    # ============ Tipos de Fotos ============
    logger.info("  → Insertando Tipos de Fotos...")
    if db.query(TipoFoto).count() == 0:
        db.add_all(
            [
                TipoFoto(nombre="banner"),
                TipoFoto(nombre="capturas"),
            ]
        )
        db.commit()
        logger.info("    ✓ Tipos de Fotos insertados")
    else:
        logger.info("    Tipos de Fotos ya existen")

    # ============ Categorias de Productos ============
    logger.info("  → Insertando Categorias de Productos...")
    if db.query(Categoria).count() == 0:
        db.add_all(
            [
                Categoria(nombre="Entradas"),
                Categoria(nombre="Platos Principales"),
                Categoria(nombre="Postres"),
                Categoria(nombre="Bebidas"),
                Categoria(nombre="Cervezas"),
                Categoria(nombre="Vinos"),
                Categoria(nombre="Cocteles"),
                Categoria(nombre="Cafés"),
            ]
        )
        db.commit()
        logger.info("    ✓ Categorias insertadas")
    else:
        logger.info("    Categorias ya existen")
