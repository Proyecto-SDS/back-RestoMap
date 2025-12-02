import logging
from database import SessionLocal, engine, Base
from models import (
    Rol, Comuna, TipoLocal, TipoFoto, TipoRed, Categoria,
    Direccion, Local, Horario, Mesa, Redes, Foto,
    TipoHorarioEnum, EstadoMesaEnum, RolEnum
)
from datetime import date, time

logger = logging.getLogger(__name__)

def seed_database():
    """
    Puebla la base de datos de manera SEGURA.
    No borra tablas. Solo agrega datos si las tablas están vacías.
    """
    logger.info("🛡️ Iniciando Seed Seguro (Sin borrar datos)...")
    
    # 1. Asegurar que las tablas existan (Esto es seguro, no sobrescribe)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # --- DATOS MAESTROS ---
        
        # Roles
        if db.query(Rol).count() == 0:
            logger.info("   -> Creando Roles...")
            db.add_all([
                Rol(id=1, nombre="admin"),
                Rol(id=2, nombre="gerente"),
                Rol(id=3, nombre="cliente")
            ])
            db.commit()

        # Comunas
        if db.query(Comuna).count() == 0:
            logger.info("   -> Creando Comunas...")
            db.add_all([
                Comuna(id=1, nombre="Santiago"),
                Comuna(id=14, nombre="Las Condes"),
                Comuna(id=23, nombre="Providencia")
            ])
            db.commit()

        # Tipos de Local
        if db.query(TipoLocal).count() == 0:
            logger.info("   -> Creando Tipos de Local...")
            db.add_all([
                TipoLocal(id=1, nombre="Restaurante"),
                TipoLocal(id=2, nombre="Bar"),
                TipoLocal(id=3, nombre="Restobar")
            ])
            db.commit()
            
        # Tipos de Foto
        if db.query(TipoFoto).count() == 0:
            db.add_all([TipoFoto(id=1, nombre="banner"), TipoFoto(id=2, nombre="logo")])
            db.commit()

        # Tipos de Red
        if db.query(TipoRed).count() == 0:
            db.add_all([TipoRed(id=1, nombre="website"), TipoRed(id=2, nombre="instagram")])
            db.commit()

        # --- DATOS DE PRUEBA (LOCALES) ---
        
        # Solo insertamos locales si NO existen
        if db.query(Local).count() == 0:
            logger.info("   -> Creando Locales de Ejemplo...")
            
            # Dirección 1
            dir1 = Direccion(id_comuna=1, calle="Av. Prueba", numero=123, longitud=-70.6, latitud=-33.4)
            db.add(dir1)
            db.commit() # Commit para obtener ID
            
            # Local 1
            local1 = Local(
                id_direccion=dir1.id,
                id_tipo_local=1,
                nombre="Restaurante Demo Cloud",
                descripcion="Local generado automáticamente para pruebas.",
                telefono=99999999,
                correo="demo@cloud.com"
            )
            db.add(local1)
            db.commit()
            
            # Horarios Local 1
            for dia in range(1, 8):
                db.add(Horario(
                    id_local=local1.id, tipo=TipoHorarioEnum.NORMAL,
                    fecha_inicio=date(2024, 1, 1), fecha_fin=date(2030, 12, 31),
                    dia_semana=dia, hora_apertura=time(12, 0), hora_cierre=time(23, 0),
                    abierto=True
                ))
            
            # Mesas Local 1
            for i in range(1, 6):
                db.add(Mesa(id_local=local1.id, nombre=f"Mesa {i}", capacidad=4, estado=EstadoMesaEnum.DISPONIBLE))
                
            db.commit()
            logger.info("   ✅ Locales creados.")
        else:
            logger.info("   ℹ️ Ya existen locales. Se omite la inserción.")

        logger.info("✅ Seed Seguro finalizado con éxito.")

    except Exception as e:
        logger.error(f"❌ Error en Seed: {e}")
        db.rollback()
        raise e
    finally:
        db.close()