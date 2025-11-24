import modelos

from db.sesion import SessionLocal
from modelos.rol import Rol
from modelos.tipo_local import TipoLocal
from modelos.comuna import Comuna
from modelos.tipo_red import TipoRed
from modelos.tipo_foto import TipoFoto

def tablas_fijas():
    db = SessionLocal()
    try:

        # Roles
        existing = db.query(Rol).count()
        if existing == 0:
            db.add_all([
                Rol(nombre="admin"),
                Rol(nombre="mesero"),
                Rol(nombre="cliente"),
            ])

        # Tipo_Local
        if db.query(TipoLocal).count() == 0:
            db.add_all([
                TipoLocal(nombre="Restaurante"),
                TipoLocal(nombre="Bar"),
                TipoLocal(nombre="Cafetería"),
            ])

        # Comunas
        if db.query(Comuna).count() == 0:
            db.add_all([
                Comuna(nombre="Santiago"),
                Comuna(nombre="Cerrillos"),
                Comuna(nombre="Cerro Navia"),
                Comuna(nombre="Conchalí"),
                Comuna(nombre="El Bosque"),
                Comuna(nombre="Estación Central"),
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
                Comuna(nombre="San Joaquín"),
                Comuna(nombre="San Miguel"),
                Comuna(nombre="San Ramón"),
                Comuna(nombre="Vitacura")
            ])

        # Tipo_Red
        if db.query(TipoRed).count() == 0:
            db.add_all([
                TipoRed(nombre="Sitio Web"),
                TipoRed(nombre="Instagram"),
                TipoRed(nombre="Facebook"),
                TipoRed(nombre="TikTok"),
                TipoRed(nombre="YouTube"),
                TipoRed(nombre="X/Twitter"),
                TipoRed(nombre="Whatsapp")
            ])

        # Tipo_Foto
        if db.query(TipoFoto).count() == 0:
            db.add_all([
                # imagen
                TipoFoto(nombre="banner"),
                TipoFoto(nombre="hero"),
                TipoFoto(nombre="icono"),
                TipoFoto(nombre="logo"),
                TipoFoto(nombre="promocion"),
                # producto
                TipoFoto(nombre="producto"),
                TipoFoto(nombre="ingredientes"),
                TipoFoto(nombre="menu"),
                # local
                TipoFoto(nombre="interior"),
                TipoFoto(nombre="exterior"),
                TipoFoto(nombre="fachada"),
                TipoFoto(nombre="mesa"),
                # staff del local
                TipoFoto(nombre="staff"),
            ])

        db.commit()
        
    finally:
        db.close()

if __name__ == "__main__":
    tablas_fijas()