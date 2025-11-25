"""
Script de Seed (Datos Iniciales)
Puebla la base de datos con datos de referencia y ejemplos de testing
"""
import os
import sys
from datetime import datetime, date, time, timedelta
from dotenv import load_dotenv

# Añadir src al path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database import db_session
from models.models import (
    Rol, TipoLocal, Comuna, TipoRed, TipoFoto, Direccion, Local, Categoria,
    Usuario, Horario, Mesa, Producto, Foto, Redes, Opinion, Favorito,
    Reserva, ReservaMesa, Pedido, Cuenta, EstadoPedido, QRDinamico,
    Encomienda, EncomiendaCuenta, Pago,
    EstadoMesaEnum, EstadoPedidoEnum, EstadoProductoEnum, EstadoReservaEnum,
    EstadoReservaMesaEnum, EstadoPagoEnum, MetodoPagoEnum, EstadoEncomiendaEnum,
    TipoHorarioEnum
)

def seed_database():
    """Pobla la base de datos con datos iniciales"""
    db = db_session()
    print("Poblando base de datos con datos iniciales...")
    
    try:
        # ============ Roles ============
        if db.query(Rol).count() == 0:
            print("  → Insertando Roles...")
            db.add_all([
                Rol(nombre="admin"),
                Rol(nombre="gerente"),
                Rol(nombre="chef"),
                Rol(nombre="mesero"),
                Rol(nombre="cliente"),
            ])
            db.commit()
            print("    ✓ Roles insertados")
        else:
            print("  ⊘ Roles ya existen, saltando...")

        # ============ Tipos de Local ============
        if db.query(TipoLocal).count() == 0:
            print("  → Insertando Tipos de Local...")
            db.add_all([
                TipoLocal(nombre="Restaurante"),
                TipoLocal(nombre="Bar"),
                TipoLocal(nombre="Restobar"),
            ])
            db.commit()
            print("    ✓ Tipos de Local insertados")
        else:
            print("  ⊘ Tipos de Local ya existen, saltando...")

        # ============ Comunas ============
        if db.query(Comuna).count() == 0:
            print("  → Insertando Comunas de Santiago...")
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
                Comuna(nombre="Vitacura"),
            ])
            db.commit()
            print("    ✓ Comunas insertadas")
        else:
            print("  ⊘ Comunas ya existen, saltando...")

        # ============ Tipos de Redes Sociales ============
        if db.query(TipoRed).count() == 0:
            print("  → Insertando Tipos de Redes Sociales...")
            db.add_all([
                TipoRed(nombre="Sitio Web"),
                TipoRed(nombre="Instagram"),
                TipoRed(nombre="Facebook"),
                TipoRed(nombre="TikTok"),
                TipoRed(nombre="YouTube"),
                TipoRed(nombre="X/Twitter"),
                TipoRed(nombre="WhatsApp"),
                TipoRed(nombre="LinkedIn"),
            ])
            db.commit()
            print("    ✓ Tipos de Redes Sociales insertados")
        else:
            print("  ⊘ Tipos de Redes Sociales ya existen, saltando...")

        # ============ Tipos de Fotos ============
        if db.query(TipoFoto).count() == 0:
            print("  → Insertando Tipos de Fotos...")
            db.add_all([
                TipoFoto(nombre="banner"),
                TipoFoto(nombre="hero"),
                TipoFoto(nombre="icono"),
                TipoFoto(nombre="logo"),
                TipoFoto(nombre="promocion"),
                TipoFoto(nombre="producto"),
                TipoFoto(nombre="ingredientes"),
                TipoFoto(nombre="menu"),
                TipoFoto(nombre="interior"),
                TipoFoto(nombre="exterior"),
                TipoFoto(nombre="fachada"),
                TipoFoto(nombre="mesa"),
                TipoFoto(nombre="staff"),
                TipoFoto(nombre="galeria"),
            ])
            db.commit()
            print("    ✓ Tipos de Fotos insertados")
        else:
            print("  ⊘ Tipos de Fotos ya existen, saltando...")

        # ============ Categorías de Productos ============
        if db.query(Categoria).count() == 0:
            print("  → Insertando Categorías de Productos...")
            db.add_all([
                Categoria(nombre="Entradas"),
                Categoria(nombre="Platos Principales"),
                Categoria(nombre="Postres"),
                Categoria(nombre="Bebidas"),
                Categoria(nombre="Cervezas"),
                Categoria(nombre="Vinos"),
                Categoria(nombre="Cócteles"),
                Categoria(nombre="Cafés"),
            ])
            db.commit()
            print("    ✓ Categorías insertadas")
        else:
            print("  ⊘ Categorías ya existen, saltando...")

        # ============ DATOS DE EJEMPLO (Para testing) ============
        
        # Direcciones de ejemplo
        if db.query(Direccion).count() == 0:
            print("  → Insertando Direcciones de ejemplo...")
            dir1 = Direccion(id_comuna=1, calle="Av. Libertador Bernardo O'Higgins", numero=123, longitud=-70.64827, latitud=-33.45694)
            dir2 = Direccion(id_comuna=23, calle="Av. Providencia", numero=456, longitud=-70.61203, latitud=-33.4314)
            dir3 = Direccion(id_comuna=14, calle="Av. Apoquindo", numero=789, longitud=-70.5679, latitud=-33.4132)
            dir4 = Direccion(id_comuna=1, calle="Calle Moneda", numero=101, longitud=-70.6506, latitud=-33.4378)
            dir5 = Direccion(id_comuna=23, calle="Av. General Bustamante", numero=202, longitud=-70.605, latitud=-33.426)
            db.add_all([dir1, dir2, dir3, dir4, dir5])
            db.commit()
            print("    ✓ Direcciones de ejemplo insertadas")
        else:
            print("  ⊘ Direcciones ya existen, saltando...")

        # Locales de ejemplo
        if db.query(Local).count() == 0:
            print("  → Insertando Locales de ejemplo...")
            local1 = Local(
                id_direccion=1, 
                id_tipo_local=1, 
                nombre="El Gran Sabor", 
                descripcion="Restaurante de comida chilena tradicional con ambiente familiar. Especialidad en platos típicos y carnes a la parrilla.",
                telefono=123456789, 
                correo="contacto@gransabor.cl"
            )
            local2 = Local(
                id_direccion=2, 
                id_tipo_local=2, 
                nombre="Bar La Terraza", 
                descripcion="Bar con terraza al aire libre, ideal para después de la oficina. Amplia carta de cervezas artesanales y cócteles.",
                telefono=987654321, 
                correo="reservas@laterraza.cl"
            )
            local3 = Local(
                id_direccion=3, 
                id_tipo_local=3, 
                nombre="Restobar del Parque", 
                descripcion="Restobar moderno con música en vivo los fines de semana. Fusión de cocina internacional y bar de tragos premium.",
                telefono=555666777, 
                correo="info@restobarparque.com"
            )
            local4 = Local(
                id_direccion=4, 
                id_tipo_local=1, 
                nombre="Rincón Peruano", 
                descripcion="Auténtica comida peruana en el corazón de Santiago. Especialidad en ceviches, tiraditos y causas limeñas.",
                telefono=111222333, 
                correo="contacto@rinconperuano.cl"
            )
            local5 = Local(
                id_direccion=5, 
                id_tipo_local=2, 
                nombre="The Old Pub", 
                descripcion="Pub estilo inglés con ambiente acogedor. Amplia selección de cervezas importadas y comida de pub clásica.",
                telefono=444555666, 
                correo="contact@theoldpub.com"
            )
            db.add_all([local1, local2, local3, local4, local5])
            db.commit()
            print("    ✓ Locales de ejemplo insertados")
        else:
            print("  ⊘ Locales ya existen, saltando...")

        # ============ Horarios ============
        if db.query(Horario).count() == 0:
            print("  → Insertando Horarios de ejemplo...")
            # Horarios para Local 1 - Restaurante (Lun-Dom 11:00-20:00)
            for dia in range(1, 8):
                db.add(Horario(
                    id_local=1, tipo=TipoHorarioEnum.NORMAL,
                    fecha_inicio=date(2024, 1, 1), fecha_fin=date(2025, 12, 31),
                    dia_semana=dia, hora_apertura=time(11, 0), hora_cierre=time(20, 0),
                    abierto=True
                ))
            # Horarios para Local 2 - Bar (Lun-Dom 17:00-23:00)
            for dia in range(1, 8):
                db.add(Horario(
                    id_local=2, tipo=TipoHorarioEnum.NORMAL,
                    fecha_inicio=date(2024, 1, 1), fecha_fin=date(2025, 12, 31),
                    dia_semana=dia, hora_apertura=time(17, 0), hora_cierre=time(23, 0),
                    abierto=True
                ))
            # Horarios para Local 3 - Restobar (Lun-Dom 12:00-20:00)
            for dia in range(1, 8):
                db.add(Horario(
                    id_local=3, tipo=TipoHorarioEnum.NORMAL,
                    fecha_inicio=date(2024, 1, 1), fecha_fin=date(2025, 12, 31),
                    dia_semana=dia, hora_apertura=time(12, 0), hora_cierre=time(20, 0),
                    abierto=True
                ))
            # Horarios para Local 4 - Restaurante (Lun-Dom 12:00-23:00)
            for dia in range(1, 8):
                db.add(Horario(
                    id_local=4, tipo=TipoHorarioEnum.NORMAL,
                    fecha_inicio=date(2024, 1, 1), fecha_fin=date(2025, 12, 31),
                    dia_semana=dia, hora_apertura=time(12, 0), hora_cierre=time(23, 0),
                    abierto=True
                ))
            # Horarios para Local 5 - Bar (Lun-Dom 18:00-23:00)
            for dia in range(1, 8):
                db.add(Horario(
                    id_local=5, tipo=TipoHorarioEnum.NORMAL,
                    fecha_inicio=date(2024, 1, 1), fecha_fin=date(2025, 12, 31),
                    dia_semana=dia, hora_apertura=time(18, 0), hora_cierre=time(23, 0),
                    abierto=True
                ))
            db.commit()
            print("    ✓ Horarios insertados")
        else:
            print("  ⊘ Horarios ya existen, saltando...")

        # ============ Mesas ============
        if db.query(Mesa).count() == 0:
            print("  → Insertando Mesas de ejemplo...")
            # Mesas para Local 1 - El Gran Sabor (10 mesas de 4 personas)
            for i in range(1, 11):
                db.add(Mesa(id_local=1, nombre=f"Mesa {i}", capacidad=4, estado=EstadoMesaEnum.DISPONIBLE))
            # Mesas para Local 2 - Bar La Terraza (5 mesas de 6 personas)
            for i in range(1, 6):
                db.add(Mesa(id_local=2, nombre=f"Mesa {i}", capacidad=6, estado=EstadoMesaEnum.DISPONIBLE))
            # Mesas para Local 3 - Restobar del Parque (8 mesas variadas)
            db.add(Mesa(id_local=3, nombre="Mesa 1", capacidad=2, estado=EstadoMesaEnum.DISPONIBLE))
            db.add(Mesa(id_local=3, nombre="Mesa 2", capacidad=2, estado=EstadoMesaEnum.DISPONIBLE))
            db.add(Mesa(id_local=3, nombre="Mesa 3", capacidad=4, estado=EstadoMesaEnum.DISPONIBLE))
            db.add(Mesa(id_local=3, nombre="Mesa 4", capacidad=4, estado=EstadoMesaEnum.DISPONIBLE))
            db.add(Mesa(id_local=3, nombre="Mesa 5", capacidad=4, estado=EstadoMesaEnum.DISPONIBLE))
            db.add(Mesa(id_local=3, nombre="Mesa 6", capacidad=6, estado=EstadoMesaEnum.DISPONIBLE))
            db.add(Mesa(id_local=3, nombre="Mesa 7", capacidad=6, estado=EstadoMesaEnum.DISPONIBLE))
            db.add(Mesa(id_local=3, nombre="Mesa 8", capacidad=8, estado=EstadoMesaEnum.DISPONIBLE))
            # Mesas para Local 4 - Rincón Peruano (7 mesas)
            for i in range(1, 8):
                capacidad = 4 if i <= 5 else 6
                db.add(Mesa(id_local=4, nombre=f"Mesa {i}", capacidad=capacidad, estado=EstadoMesaEnum.DISPONIBLE))
            # Mesas para Local 5 - The Old Pub (6 mesas)
            db.add(Mesa(id_local=5, nombre="Mesa 1", capacidad=4, estado=EstadoMesaEnum.DISPONIBLE))
            db.add(Mesa(id_local=5, nombre="Mesa 2", capacidad=4, estado=EstadoMesaEnum.DISPONIBLE))
            db.add(Mesa(id_local=5, nombre="Mesa 3", capacidad=6, estado=EstadoMesaEnum.DISPONIBLE))
            db.add(Mesa(id_local=5, nombre="Mesa 4", capacidad=6, estado=EstadoMesaEnum.DISPONIBLE))
            db.add(Mesa(id_local=5, nombre="Barra 1", capacidad=2, estado=EstadoMesaEnum.DISPONIBLE))
            db.add(Mesa(id_local=5, nombre="Barra 2", capacidad=2, estado=EstadoMesaEnum.DISPONIBLE))
            db.commit()
            print("    ✓ Mesas insertadas")
        else:
            print("  ⊘ Mesas ya existen, saltando...")

        # ============ Usuarios ============
        if db.query(Usuario).count() == 0:
            print("  → Insertando Usuarios de ejemplo...")
            # Hash para password: test123
            password_hash = "$2b$12$q6myteznSC8775D4zt/e6OnPZVMv4jxV9ejhmMRpubGnVA1lecciO"
            db.add_all([
                Usuario(id_rol=1, nombre="Admin Test", correo="admin@test.cl", 
                       contrasena=password_hash, 
                       telefono="912345678"),
                Usuario(id_rol=5, nombre="Juan Pérez", correo="juan@test.cl", 
                       contrasena=password_hash, 
                       telefono="987654321"),
                Usuario(id_rol=5, nombre="María González", correo="maria@test.cl", 
                       contrasena=password_hash, 
                       telefono="955556666"),
                Usuario(id_rol=4, nombre="Carlos Mesero", correo="mesero@test.cl", 
                       contrasena=password_hash, 
                       telefono="944443333"),
                Usuario(id_rol=3, nombre="Ana Chef", correo="chef@test.cl", 
                       contrasena=password_hash, 
                       telefono="933332222"),
            ])
            db.commit()
            print("    ✓ Usuarios insertados (password: test123)")
        else:
            print("  ⊘ Usuarios ya existen, saltando...")

        # ============ Productos ============
        if db.query(Producto).count() == 0:
            print("  → Insertando Productos de ejemplo...")
            # Productos para Local 1 (Restaurante)
            db.add_all([
                Producto(id_local=1, id_categoria=1, nombre="Empanadas de Pino", 
                        descripcion="3 empanadas tradicionales", estado=EstadoProductoEnum.DISPONIBLE, precio=4500),
                Producto(id_local=1, id_categoria=2, nombre="Lomo a lo Pobre", 
                        descripcion="Con papas fritas y huevos", estado=EstadoProductoEnum.DISPONIBLE, precio=9500),
                Producto(id_local=1, id_categoria=2, nombre="Pastel de Choclo", 
                        descripcion="Tradicional chileno", estado=EstadoProductoEnum.DISPONIBLE, precio=7800),
                Producto(id_local=1, id_categoria=3, nombre="Leche Asada", 
                        descripcion="Postre tradicional", estado=EstadoProductoEnum.DISPONIBLE, precio=3200),
                Producto(id_local=1, id_categoria=4, nombre="Pisco Sour", 
                        descripcion="Cóctel nacional", estado=EstadoProductoEnum.DISPONIBLE, precio=4500),
            ])
            # Productos para Local 2 (Bar)
            db.add_all([
                Producto(id_local=2, id_categoria=5, nombre="Cerveza Kunstmann", 
                        descripcion="500ml", estado=EstadoProductoEnum.DISPONIBLE, precio=3500),
                Producto(id_local=2, id_categoria=7, nombre="Mojito", 
                        descripcion="Ron, menta, lima", estado=EstadoProductoEnum.DISPONIBLE, precio=5500),
                Producto(id_local=2, id_categoria=1, nombre="Tabla de Quesos", 
                        descripcion="Selección de quesos nacionales", estado=EstadoProductoEnum.DISPONIBLE, precio=8900),
            ])
            # Productos para Local 3 (Cafetería)
            db.add_all([
                Producto(id_local=3, id_categoria=8, nombre="Café Americano", 
                        descripcion="Grande", estado=EstadoProductoEnum.DISPONIBLE, precio=2500),
                Producto(id_local=3, id_categoria=8, nombre="Cappuccino", 
                        descripcion="Grande", estado=EstadoProductoEnum.DISPONIBLE, precio=3200),
                Producto(id_local=3, id_categoria=3, nombre="Brownie de Chocolate", 
                        descripcion="Con helado", estado=EstadoProductoEnum.DISPONIBLE, precio=3800),
            ])
            db.commit()
            print("    ✓ Productos insertados")
        else:
            print("  ⊘ Productos ya existen, saltando...")

        # ============ Fotos ============
        if db.query(Foto).count() == 0:
            print("  → Insertando Fotos de ejemplo...")
            db.add_all([
                Foto(id_local=1, id_tipo_foto=1, ruta="https://picsum.photos/seed/local1banner/1200/400"),
                Foto(id_local=1, id_tipo_foto=4, ruta="https://picsum.photos/seed/local1logo/200/200"),
                Foto(id_local=2, id_tipo_foto=1, ruta="https://picsum.photos/seed/local2banner/1200/400"),
                Foto(id_local=3, id_tipo_foto=1, ruta="https://picsum.photos/seed/local3banner/1200/400"),
                Foto(id_producto=1, id_tipo_foto=6, ruta="https://picsum.photos/seed/prod1/400/400"),
                Foto(id_producto=2, id_tipo_foto=6, ruta="https://picsum.photos/seed/prod2/400/400"),
            ])
            db.commit()
            print("    ✓ Fotos insertadas")
        else:
            print("  ⊘ Fotos ya existen, saltando...")

        # ============ Redes Sociales ============
        if db.query(Redes).count() == 0:
            print("  → Insertando Redes Sociales de ejemplo...")
            db.add_all([
                Redes(id_local=1, id_tipo_red=2, nombre_usuario="@gransabor", 
                      url="https://instagram.com/gransabor"),
                Redes(id_local=1, id_tipo_red=3, nombre_usuario="El Gran Sabor", 
                      url="https://facebook.com/gransabor"),
                Redes(id_local=2, id_tipo_red=2, nombre_usuario="@laterraza", 
                      url="https://instagram.com/laterraza"),
            ])
            db.commit()
            print("    ✓ Redes Sociales insertadas")
        else:
            print("  ⊘ Redes Sociales ya existen, saltando...")

        # ============ Opiniones ============
        if db.query(Opinion).count() == 0:
            print("  → Insertando Opiniones de ejemplo...")
            db.add_all([
                Opinion(id_usuario=2, id_local=1, puntuacion=5, 
                       comentario="Excelente comida y muy buen servicio. Recomendado!"),
                Opinion(id_usuario=3, id_local=1, puntuacion=3, 
                       comentario="El mejor lomo a lo pobre de Santiago!"),
                Opinion(id_usuario=2, id_local=2, puntuacion=4, 
                       comentario="Buen ambiente, música en vivo los fines de semana."),
            ])
            db.commit()
            print("    ✓ Opiniones insertadas")
        else:
            print("  ⊘ Opiniones ya existen, saltando...")

        # ============ Favoritos ============
        if db.query(Favorito).count() == 0:
            print("  → Insertando Favoritos de ejemplo...")
            db.add_all([
                Favorito(id_usuario=2, id_local=1),
                Favorito(id_usuario=2, id_local=3),
                Favorito(id_usuario=3, id_local=1),
                Favorito(id_usuario=3, id_local=2),
            ])
            db.commit()
            print("    ✓ Favoritos insertados")
        else:
            print("  ⊘ Favoritos ya existen, saltando...")

        # ============ Reservas ============
        if db.query(Reserva).count() == 0:
            print("  → Insertando Reservas de ejemplo...")
            # Reserva confirmada
            reserva1 = Reserva(
                id_local=1, id_usuario=2,
                fecha_reserva=date.today() + timedelta(days=2),
                hora_reserva=time(20, 0),
                estado=EstadoReservaEnum.CONFIRMADA
            )
            # Reserva pendiente
            reserva2 = Reserva(
                id_local=2, id_usuario=3,
                fecha_reserva=date.today() + timedelta(days=5),
                hora_reserva=time(21, 30),
                estado=EstadoReservaEnum.PENDIENTE
            )
            db.add_all([reserva1, reserva2])
            db.commit()
            
            # Asignar mesas a reservas
            db.add_all([
                ReservaMesa(id_reserva=reserva1.id, id_mesa=1, prioridad=EstadoReservaMesaEnum.ALTA),
                ReservaMesa(id_reserva=reserva1.id, id_mesa=2, prioridad=EstadoReservaMesaEnum.MEDIA),
                ReservaMesa(id_reserva=reserva2.id, id_mesa=6, prioridad=EstadoReservaMesaEnum.ALTA),
            ])
            db.commit()
            print("    ✓ Reservas insertadas")
        else:
            print("  ⊘ Reservas ya existen, saltando...")

        # ============ Pedidos ============
        if db.query(Pedido).count() == 0:
            print("  → Insertando Pedidos de ejemplo...")
            # Pedido abierto
            pedido1 = Pedido(
                local_id=1, mesa_id=3, usuario_id=2,
                estado=EstadoPedidoEnum.ABIERTO, total=14000
            )
            # Pedido en preparación
            pedido2 = Pedido(
                local_id=1, mesa_id=4, usuario_id=3,
                estado=EstadoPedidoEnum.EN_PREPARACION, total=25300
            )
            # Pedido cerrado (histórico)
            pedido3 = Pedido(
                local_id=2, mesa_id=7, usuario_id=2,
                estado=EstadoPedidoEnum.CERRADO, total=18500,
                creado_el=datetime.now() - timedelta(days=1)
            )
            db.add_all([pedido1, pedido2, pedido3])
            db.commit()
            
            # Cuentas para pedido 1
            db.add_all([
                Cuenta(id_pedido=pedido1.id, id_producto=1, cantidad=2, observaciones="Sin cebolla"),
                Cuenta(id_pedido=pedido1.id, id_producto=5, cantidad=1, observaciones=""),
            ])
            # Cuentas para pedido 2
            db.add_all([
                Cuenta(id_pedido=pedido2.id, id_producto=2, cantidad=1, observaciones="Término medio"),
                Cuenta(id_pedido=pedido2.id, id_producto=3, cantidad=2, observaciones=""),
            ])
            # Cuentas para pedido 3
            db.add_all([
                Cuenta(id_pedido=pedido3.id, id_producto=6, cantidad=3, observaciones=""),
                Cuenta(id_pedido=pedido3.id, id_producto=8, cantidad=2, observaciones=""),
            ])
            db.commit()
            
            # Estados de pedido
            db.add_all([
                EstadoPedido(pedido_id=pedido1.id, estado=EstadoPedidoEnum.ABIERTO, creado_por=4),
                EstadoPedido(pedido_id=pedido2.id, estado=EstadoPedidoEnum.ABIERTO, creado_por=4,
                           creado_el=datetime.now() - timedelta(minutes=30)),
                EstadoPedido(pedido_id=pedido2.id, estado=EstadoPedidoEnum.EN_PREPARACION, creado_por=5,
                           creado_el=datetime.now() - timedelta(minutes=15)),
                EstadoPedido(pedido_id=pedido3.id, estado=EstadoPedidoEnum.CERRADO, creado_por=4,
                           creado_el=datetime.now() - timedelta(days=1)),
            ])
            db.commit()
            print("    ✓ Pedidos, Cuentas y Estados insertados")
        else:
            print("  ⊘ Pedidos ya existen, saltando...")

        # ============ Pagos ============
        if db.query(Pago).count() == 0:
            print("  → Insertando Pagos de ejemplo...")
            # Pago del pedido cerrado
            db.add(Pago(
                pedido_id=3, metodo=MetodoPagoEnum.CREDITO,
                estado=EstadoPagoEnum.COBRADO, monto=18500,
                creado_el=datetime.now() - timedelta(days=1)
            ))
            # Pago pendiente para pedido en preparación
            db.add(Pago(
                pedido_id=2, metodo=MetodoPagoEnum.EFECTIVO,
                estado=EstadoPagoEnum.PENDIENTE, monto=25300
            ))
            db.commit()
            print("    ✓ Pagos insertados")
        else:
            print("  ⊘ Pagos ya existen, saltando...")

        # ============ QR Dinámicos ============
        if db.query(QRDinamico).count() == 0:
            print("  → Insertando QR Dinámicos de ejemplo...")
            db.add_all([
                QRDinamico(
                    id_mesa=3, id_pedido=1, codigo="QR-M3-P1-ABC123",
                    expiracion=datetime.now() + timedelta(hours=4), activo=True
                ),
                QRDinamico(
                    id_mesa=4, id_pedido=2, codigo="QR-M4-P2-XYZ789",
                    expiracion=datetime.now() + timedelta(hours=4), activo=True
                ),
            ])
            db.commit()
            print("    ✓ QR Dinámicos insertados")
        else:
            print("  ⊘ QR Dinámicos ya existen, saltando...")

        # ============ Encomiendas ============
        if db.query(Encomienda).count() == 0:
            print("  → Insertando Encomiendas de ejemplo...")
            enc1 = Encomienda(id_pedido=2, estado=EstadoEncomiendaEnum.EN_PREPARACION)
            db.add(enc1)
            db.commit()
            
            # Vincular cuenta con encomienda
            db.add(EncomiendaCuenta(id_cuenta=3, id_encomienda=enc1.id))
            db.commit()
            print("    ✓ Encomiendas insertadas")
        else:
            print("  ⊘ Encomiendas ya existen, saltando...")
        
        print("\nBase de datos poblada exitosamente con datos completos!")
        print("\nResumen de datos insertados:")
        print(f"   • Roles: {db.query(Rol).count()}")
        print(f"   • Usuarios: {db.query(Usuario).count()}")
        print(f"   • Locales: {db.query(Local).count()}")
        print(f"   • Mesas: {db.query(Mesa).count()}")
        print(f"   • Productos: {db.query(Producto).count()}")
        print(f"   • Pedidos: {db.query(Pedido).count()}")
        print(f"   • Reservas: {db.query(Reserva).count()}")
        print(f"   • Opiniones: {db.query(Opinion).count()}")
        print(f"   • Pagos: {db.query(Pago).count()}")
        
    except Exception as e:
        print(f"\nError al poblar la base de datos: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    # Cargar variables de entorno
    load_dotenv()
    
    # Ejecutar seed
    seed_database()