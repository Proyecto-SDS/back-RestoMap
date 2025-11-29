import logging
from models import Opinion, Favorito

logger = logging.getLogger(__name__)

def create_interactions(db):
    # ============ Opiniones ============
    logger.info("  → Insertando Opiniones de ejemplo...")
    if db.query(Opinion).count() == 0:
        db.add_all([
            Opinion(id_usuario=2, id_local=1, puntuacion=5, 
                   comentario="Excelente comida y muy buen servicio. Recomendado!"),
            Opinion(id_usuario=3, id_local=1, puntuacion=3, 
                   comentario="El mejor lomo a lo pobre de Santiago!"),
            Opinion(id_usuario=2, id_local=2, puntuacion=4, 
                   comentario="Buen ambiente, música en vivo los fines de semana."),
        ])
        db.commit()
        logger.info("    ✓ Opiniones insertadas")
    else:
        logger.info("    ⚠ Opiniones ya existen")

    # ============ Favoritos ============
    logger.info("  → Insertando Favoritos de ejemplo...")
    if db.query(Favorito).count() == 0:
        db.add_all([
            Favorito(id_usuario=2, id_local=1),
            Favorito(id_usuario=2, id_local=3),
            Favorito(id_usuario=3, id_local=1),
            Favorito(id_usuario=3, id_local=2),
        ])
        db.commit()
        logger.info("    ✓ Favoritos insertados")
    else:
        logger.info("    ⚠ Favoritos ya existen")
