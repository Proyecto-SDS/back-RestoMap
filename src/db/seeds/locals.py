from datetime import date, time

from config import get_logger
from models import (
    Categoria,
    Direccion,
    EstadoMesaEnum,
    Foto,
    Horario,
    Local,
    Mesa,
    Redes,
    TipoHorarioEnum,
)

logger = get_logger(__name__)


def create_locals(db):
    # ============ Direcciones ============
    logger.info("  → Insertando Direcciones de ejemplo...")
    if db.query(Direccion).count() == 0:
        dir1 = Direccion(
            id_comuna=1,
            calle="Av. Libertador Bernardo O'Higgins",
            numero=123,
            longitud=-70.64827,
            latitud=-33.45694,
        )
        dir2 = Direccion(
            id_comuna=23,
            calle="Av. Providencia",
            numero=456,
            longitud=-70.61203,
            latitud=-33.4314,
        )
        dir3 = Direccion(
            id_comuna=14,
            calle="Av. Apoquindo",
            numero=789,
            longitud=-70.5679,
            latitud=-33.4132,
        )
        dir4 = Direccion(
            id_comuna=1,
            calle="Calle Moneda",
            numero=101,
            longitud=-70.6506,
            latitud=-33.4378,
        )
        dir5 = Direccion(
            id_comuna=23,
            calle="Av. General Bustamante",
            numero=202,
            longitud=-70.605,
            latitud=-33.426,
        )
        db.add_all([dir1, dir2, dir3, dir4, dir5])
        db.commit()
        logger.info("    ✓ Direcciones de ejemplo insertadas")
    else:
        logger.info("    Direcciones ya existen")

    # ============ Locales ============
    logger.info("  → Insertando Locales de ejemplo...")
    if db.query(Local).count() == 0:
        from datetime import datetime

        local1 = Local(
            id_direccion=1,
            id_tipo_local=1,
            nombre="El Gran Sabor",
            descripcion="Restaurante de comida chilena tradicional con ambiente familiar. Especialidad en platos tipicos y carnes a la parrilla.",
            telefono=123456789,
            correo="contacto@gransabor.cl",
            rut_empresa="76123456-7",
            razon_social="RESTAURANTE EL GRAN SABOR SPA",
            glosa_giro="RESTAURANTES, BARES Y CANTINAS",
            terminos_aceptados=True,
            fecha_aceptacion_terminos=datetime.now(),
            version_terminos="v1.0",
        )
        local2 = Local(
            id_direccion=2,
            id_tipo_local=2,
            nombre="Bar La Terraza",
            descripcion="Bar con terraza al aire libre, ideal para después de la oficina. Amplia carta de cervezas artesanales y cocteles.",
            telefono=987654321,
            correo="reservas@laterraza.cl",
            rut_empresa="76234567-8",
            razon_social="BAR LA TERRAZA LTDA",
            glosa_giro="BARES, PUBS Y DISCOTECAS",
            terminos_aceptados=True,
            fecha_aceptacion_terminos=datetime.now(),
            version_terminos="v1.0",
        )
        local3 = Local(
            id_direccion=3,
            id_tipo_local=3,
            nombre="Restobar del Parque",
            descripcion="Restobar moderno con música en vivo los fines de semana. Fusion de cocina internacional y bar de tragos premium.",
            telefono=555666777,
            correo="info@restobarparque.com",
            rut_empresa="76345678-9",
            razon_social="RESTOBAR DEL PARQUE SPA",
            glosa_giro="RESTAURANTES, BARES Y CANTINAS",
            terminos_aceptados=True,
            fecha_aceptacion_terminos=datetime.now(),
            version_terminos="v1.0",
        )
        local4 = Local(
            id_direccion=4,
            id_tipo_local=1,
            nombre="Rincon Peruano",
            descripcion="Auténtica comida peruana en el corazon de Santiago. Especialidad en ceviches, tiraditos y causas limeñas.",
            telefono=111222333,
            correo="contacto@rinconperuano.cl",
            rut_empresa="76456789-0",
            razon_social="RINCON PERUANO EIRL",
            glosa_giro="RESTAURANTES, BARES Y CANTINAS",
            terminos_aceptados=True,
            fecha_aceptacion_terminos=datetime.now(),
            version_terminos="v1.0",
        )
        local5 = Local(
            id_direccion=5,
            id_tipo_local=2,
            nombre="The Old Pub",
            descripcion="Pub estilo inglés con ambiente acogedor. Amplia seleccion de cervezas importadas y comida de pub clasica.",
            telefono=444555666,
            correo="contact@theoldpub.com",
            rut_empresa="76567890-1",
            razon_social="THE OLD PUB LTDA",
            glosa_giro="BARES, PUBS Y DISCOTECAS",
            terminos_aceptados=True,
            fecha_aceptacion_terminos=datetime.now(),
            version_terminos="v1.0",
        )
        db.add_all([local1, local2, local3, local4, local5])
        db.commit()
        logger.info("    ✓ Locales de ejemplo insertados")
    else:
        logger.info("    Locales ya existen")

    # ============ Categorias por Local ============
    logger.info("  → Insertando Categorías de ejemplo...")
    if db.query(Categoria).count() == 0:
        # Lista de categorías base que cada local tendrá
        categorias_base = [
            # Comida (id_tipo_categoria=1)
            ("Entradas", 1),
            ("Platos Principales", 1),
            ("Postres", 1),
            # Bebida (id_tipo_categoria=2)
            ("Bebidas", 2),
            ("Cervezas", 2),
            ("Vinos", 2),
            ("Cocteles", 2),
            ("Cafes", 2),
        ]

        # Crear categorías para cada local (1 al 5)
        for id_local in range(1, 6):
            for nombre, tipo_id in categorias_base:
                db.add(
                    Categoria(
                        id_local=id_local,
                        nombre=nombre,
                        id_tipo_categoria=tipo_id,
                    )
                )
        db.commit()
        logger.info("    ✓ Categorías insertadas para todos los locales")
    else:
        logger.info("    Categorías ya existen")

    # ============ Horarios ============
    logger.info("  → Insertando Horarios de ejemplo...")
    if db.query(Horario).count() == 0:
        # Horarios para Local 1 - Restaurante (Lun-Dom 11:00-20:00)
        for dia in range(1, 8):
            db.add(
                Horario(
                    id_local=1,
                    tipo=TipoHorarioEnum.NORMAL,
                    fecha_inicio=date(2024, 1, 1),
                    fecha_fin=date(2025, 12, 31),
                    dia_semana=dia,
                    hora_apertura=time(11, 0),
                    hora_cierre=time(20, 0),
                    abierto=True,
                )
            )
        # Horarios para Local 2 - Bar (Lun-Dom 17:00-23:00)
        for dia in range(1, 8):
            db.add(
                Horario(
                    id_local=2,
                    tipo=TipoHorarioEnum.NORMAL,
                    fecha_inicio=date(2024, 1, 1),
                    fecha_fin=date(2025, 12, 31),
                    dia_semana=dia,
                    hora_apertura=time(17, 0),
                    hora_cierre=time(23, 0),
                    abierto=True,
                )
            )
        # Horarios para Local 3 - Restobar (Lun-Dom 12:00-20:00)
        for dia in range(1, 8):
            db.add(
                Horario(
                    id_local=3,
                    tipo=TipoHorarioEnum.NORMAL,
                    fecha_inicio=date(2024, 1, 1),
                    fecha_fin=date(2025, 12, 31),
                    dia_semana=dia,
                    hora_apertura=time(12, 0),
                    hora_cierre=time(20, 0),
                    abierto=True,
                )
            )
        # Horarios para Local 4 - Restaurante (Lun-Dom 12:00-23:00)
        for dia in range(1, 8):
            db.add(
                Horario(
                    id_local=4,
                    tipo=TipoHorarioEnum.NORMAL,
                    fecha_inicio=date(2024, 1, 1),
                    fecha_fin=date(2025, 12, 31),
                    dia_semana=dia,
                    hora_apertura=time(12, 0),
                    hora_cierre=time(23, 0),
                    abierto=True,
                )
            )
        # Horarios para Local 5 - Bar (Lun-Dom 18:00-23:00)
        for dia in range(1, 8):
            db.add(
                Horario(
                    id_local=5,
                    tipo=TipoHorarioEnum.NORMAL,
                    fecha_inicio=date(2024, 1, 1),
                    fecha_fin=date(2025, 12, 31),
                    dia_semana=dia,
                    hora_apertura=time(18, 0),
                    hora_cierre=time(23, 0),
                    abierto=True,
                )
            )
        db.commit()
        logger.info("    ✓ Horarios insertados")
    else:
        logger.info("    Horarios ya existen")

    # ============ Mesas ============
    logger.info("  → Insertando Mesas de ejemplo...")
    if db.query(Mesa).count() == 0:
        # Mesas para Local 1 - El Gran Sabor (10 mesas de 4 personas)
        for i in range(1, 11):
            db.add(
                Mesa(
                    id_local=1,
                    nombre=f"Mesa {i}",
                    descripcion="Mesa para 4 personas - Zona principal",
                    capacidad=4,
                    orden=i,
                    estado=EstadoMesaEnum.DISPONIBLE,
                )
            )
        # Mesas para Local 2 - Bar La Terraza (5 mesas de 6 personas)
        for i in range(1, 6):
            db.add(
                Mesa(
                    id_local=2,
                    nombre=f"Mesa {i}",
                    descripcion="Mesa para 6 personas - Terraza",
                    capacidad=6,
                    orden=i,
                    estado=EstadoMesaEnum.DISPONIBLE,
                )
            )
        # Mesas para Local 3 - Restobar del Parque (8 mesas variadas)
        db.add(
            Mesa(
                id_local=3,
                nombre="Mesa 1",
                descripcion="Mesa intima junto a la ventana",
                capacidad=2,
                orden=1,
                estado=EstadoMesaEnum.DISPONIBLE,
            )
        )
        db.add(
            Mesa(
                id_local=3,
                nombre="Mesa 2",
                descripcion="Mesa intima en el balcon",
                capacidad=2,
                orden=2,
                estado=EstadoMesaEnum.DISPONIBLE,
            )
        )
        db.add(
            Mesa(
                id_local=3,
                nombre="Mesa 3",
                descripcion="Mesa estandar",
                capacidad=4,
                orden=3,
                estado=EstadoMesaEnum.DISPONIBLE,
            )
        )
        db.add(
            Mesa(
                id_local=3,
                nombre="Mesa 4",
                descripcion="Mesa estandar",
                capacidad=4,
                orden=4,
                estado=EstadoMesaEnum.DISPONIBLE,
            )
        )
        db.add(
            Mesa(
                id_local=3,
                nombre="Mesa 5",
                descripcion="Mesa estandar",
                capacidad=4,
                orden=5,
                estado=EstadoMesaEnum.DISPONIBLE,
            )
        )
        db.add(
            Mesa(
                id_local=3,
                nombre="Mesa 6",
                descripcion="Mesa familiar",
                capacidad=6,
                orden=6,
                estado=EstadoMesaEnum.DISPONIBLE,
            )
        )
        db.add(
            Mesa(
                id_local=3,
                nombre="Mesa 7",
                descripcion="Mesa familiar",
                capacidad=6,
                orden=7,
                estado=EstadoMesaEnum.DISPONIBLE,
            )
        )
        db.add(
            Mesa(
                id_local=3,
                nombre="Mesa 8",
                descripcion="Mesa grande para grupos",
                capacidad=8,
                orden=8,
                estado=EstadoMesaEnum.DISPONIBLE,
            )
        )
        # Mesas para Local 4 - Rincon Peruano (7 mesas)
        for i in range(1, 8):
            capacidad = 4 if i <= 5 else 6
            desc = "Mesa estandar" if capacidad == 4 else "Mesa familiar"
            db.add(
                Mesa(
                    id_local=4,
                    nombre=f"Mesa {i}",
                    descripcion=desc,
                    capacidad=capacidad,
                    orden=i,
                    estado=EstadoMesaEnum.DISPONIBLE,
                )
            )
        # Mesas para Local 5 - The Old Pub (6 mesas)
        db.add(
            Mesa(
                id_local=5,
                nombre="Mesa 1",
                descripcion="Mesa estandar",
                capacidad=4,
                orden=1,
                estado=EstadoMesaEnum.DISPONIBLE,
            )
        )
        db.add(
            Mesa(
                id_local=5,
                nombre="Mesa 2",
                descripcion="Mesa estandar",
                capacidad=4,
                orden=2,
                estado=EstadoMesaEnum.DISPONIBLE,
            )
        )
        db.add(
            Mesa(
                id_local=5,
                nombre="Mesa 3",
                descripcion="Mesa grande",
                capacidad=6,
                orden=3,
                estado=EstadoMesaEnum.DISPONIBLE,
            )
        )
        db.add(
            Mesa(
                id_local=5,
                nombre="Mesa 4",
                descripcion="Mesa grande",
                capacidad=6,
                orden=4,
                estado=EstadoMesaEnum.DISPONIBLE,
            )
        )
        db.add(
            Mesa(
                id_local=5,
                nombre="Barra 1",
                descripcion="Asiento en barra alta",
                capacidad=2,
                orden=5,
                estado=EstadoMesaEnum.DISPONIBLE,
            )
        )
        db.add(
            Mesa(
                id_local=5,
                nombre="Barra 2",
                descripcion="Asiento en barra alta",
                capacidad=2,
                orden=6,
                estado=EstadoMesaEnum.DISPONIBLE,
            )
        )
        db.commit()
        logger.info("    ✓ Mesas insertadas")
    else:
        logger.info("    Mesas ya existen")

    # ============ Redes Sociales ============
    logger.info("  → Insertando Redes Sociales de ejemplo...")
    if db.query(Redes).count() == 0:
        db.add_all(
            [
                Redes(
                    id_local=1,
                    id_tipo_red=2,
                    nombre_usuario="gransabor",
                    url="https://instagram.com/gransabor",
                ),
                Redes(
                    id_local=1,
                    id_tipo_red=3,
                    nombre_usuario="El Gran Sabor",
                    url="https://facebook.com/gransabor",
                ),
                Redes(
                    id_local=2,
                    id_tipo_red=2,
                    nombre_usuario="laterraza",
                    url="https://instagram.com/laterraza",
                ),
            ]
        )
        db.commit()
        logger.info("    ✓ Redes Sociales insertadas")
    else:
        logger.info("    Redes Sociales ya existen")

    # ============ Fotos ============
    logger.info("  → Insertando Fotos de ejemplo...")

    # Fotos de Locales
    if db.query(Foto).filter(Foto.id_local.isnot(None)).count() == 0:
        db.add_all(
            [
                Foto(
                    id_local=1,
                    id_tipo_foto=1,
                    ruta="https://picsum.photos/seed/local1banner/1200/400",
                ),
                Foto(
                    id_local=1,
                    id_tipo_foto=2,
                    ruta="https://picsum.photos/seed/local1logo/200/200",
                ),
                Foto(
                    id_local=2,
                    id_tipo_foto=1,
                    ruta="https://picsum.photos/seed/local2banner/1200/400",
                ),
                Foto(
                    id_local=3,
                    id_tipo_foto=1,
                    ruta="https://picsum.photos/seed/local3banner/1200/400",
                ),
                Foto(
                    id_local=4,
                    id_tipo_foto=1,
                    ruta="https://picsum.photos/seed/local4banner/1200/400",
                ),
                Foto(
                    id_local=5,
                    id_tipo_foto=1,
                    ruta="https://picsum.photos/seed/local5banner/1200/400",
                ),
            ]
        )
        db.commit()
        logger.info("    ✓ Fotos de Locales insertadas")
    else:
        logger.info("    Fotos de Locales ya existen")
