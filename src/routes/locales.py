import traceback
from datetime import datetime, time, timedelta

from flask import Blueprint, jsonify, request
from sqlalchemy.orm import joinedload

from database import db_session
from models import (
    Direccion,
    Foto,
    Local,
    Mesa,
    Opinion,
    Producto,
    Redes,
    Reserva,
    ReservaMesa,
)

# Crear el Blueprint
locales_bp = Blueprint("locales", __name__, url_prefix="/api/locales")


def add_base64_prefix(data):
    """
    Agrega el prefijo data:image/...;base64, necesario para que el navegador
    interprete la imagen correctamente si solo tenemos el string base64.
    """
    if not data:
        return None

    if data.startswith("data:"):
        return data

    if data.startswith("/9j/"):
        mime = "jpeg"
    elif data.startswith("iVBORw"):
        mime = "png"
    elif data.startswith("UklGR"):
        mime = "webp"
    else:
        mime = "jpeg"

    return f"data:image/{mime};base64,{data}"


@locales_bp.route("/", methods=["GET"])
def obtener_locales():
    """Obtiene todos los locales de la base de datos con informacion completa."""
    try:
        # Consultar locales con relaciones pre-cargadas para optimizar
        locales = (
            db_session.query(Local)
            .options(
                # pyrefly: ignore  # bad-argument-type
                joinedload(Local.direccion).joinedload(Direccion.comuna),
                # pyrefly: ignore  # bad-argument-type
                joinedload(Local.tipo_local),
                # pyrefly: ignore  # bad-argument-type
                joinedload(Local.horarios),
                # pyrefly: ignore  # bad-argument-type
                joinedload(Local.fotos).joinedload(Foto.tipo_foto),
                # pyrefly: ignore  # bad-argument-type
                joinedload(Local.opiniones),
            )
            .all()
        )

        resultado = []
        for local in locales:
            # Calcular promedio de puntuaciones
            rating = None
            review_count = 0
            if local.opiniones:
                # Filtrar opiniones no eliminadas
                opiniones_activas = [
                    op for op in local.opiniones if op.eliminado_el is None
                ]
                puntuaciones = [
                    float(op.puntuacion)
                    for op in opiniones_activas
                    if op.puntuacion is not None
                ]
                if puntuaciones:
                    rating = round(sum(puntuaciones) / len(puntuaciones), 1)
                    review_count = len(puntuaciones)

            # Determinar estado (abierto/cerrado) basado en horarios
            status = "closed"
            closing_time = None
            now = datetime.now()
            current_time = now.time()
            current_day = now.weekday() + 1  # 1 = Lunes, 7 = Domingo

            for horario in local.horarios:
                if horario.dia_semana == current_day and horario.abierto:
                    # Manejar horarios que cruzan medianoche (ej: 18:00 - 02:00)
                    if horario.hora_apertura <= horario.hora_cierre:
                        # Horario normal (no cruza medianoche)
                        if horario.hora_apertura <= current_time <= horario.hora_cierre:
                            status = "open"
                            closing_time = horario.hora_cierre.strftime("%H:%M")
                            break
                    # Horario que cruza medianoche
                    elif (
                        current_time >= horario.hora_apertura
                        or current_time <= horario.hora_cierre
                    ):
                        status = "open"
                        closing_time = horario.hora_cierre.strftime("%H:%M")
                        break

            # Obtener imagen principal
            image = None
            if local.fotos:
                # Buscar foto de tipo "banner" o tomar la primera disponible
                foto_principal = next(
                    (
                        f
                        for f in local.fotos
                        if f.tipo_foto and f.tipo_foto.nombre == "banner"
                    ),
                    None,
                )
                if foto_principal:
                    image = (
                        add_base64_prefix(foto_principal.data)
                        if foto_principal.data
                        else foto_principal.ruta
                    )
                elif local.fotos:
                    primera_foto = local.fotos[0]
                    image = (
                        add_base64_prefix(primera_foto.data)
                        if primera_foto.data
                        else primera_foto.ruta
                    )

            # Construir objeto de respuesta
            local_data = {
                "id": str(local.id),
                "name": local.nombre,
                "description": local.descripcion,
                "type": local.tipo_local.nombre if local.tipo_local else "Restaurante",
                "address": f"{local.direccion.calle} {local.direccion.numero}"
                if local.direccion and local.direccion.calle
                else "",
                "commune": local.direccion.comuna.nombre
                if local.direccion and local.direccion.comuna
                else "",
                "phone": f"+56{local.telefono}",
                "email": local.correo,
                "image": image,
                "rating": rating,
                "reviewCount": review_count,
                "status": status,
                "closingTime": closing_time,
                "coordinates": [
                    float(local.direccion.longitud) if local.direccion else -70.6693,
                    float(local.direccion.latitud) if local.direccion else -33.4489,
                ],
            }

            resultado.append(local_data)

        return jsonify(resultado), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@locales_bp.route("/<int:id>", methods=["GET"])
def obtener_local(id):
    """Obtiene un local especifico por ID con informacion detallada."""
    try:
        local = (
            db_session.query(Local)
            .options(
                # pyrefly: ignore  # bad-argument-type
                joinedload(Local.direccion).joinedload(Direccion.comuna),
                # pyrefly: ignore  # bad-argument-type
                joinedload(Local.tipo_local),
                # pyrefly: ignore  # bad-argument-type
                joinedload(Local.horarios),
                # pyrefly: ignore  # bad-argument-type
                joinedload(Local.fotos).joinedload(Foto.tipo_foto),
                # pyrefly: ignore  # bad-argument-type
                joinedload(Local.opiniones),
                # pyrefly: ignore  # bad-argument-type
                joinedload(Local.redes).joinedload(Redes.tipo_red),
            )
            .filter(Local.id == id)
            .first()
        )

        if not local:
            return jsonify({"error": "Local no encontrado"}), 404

        # Calcular promedio de puntuaciones
        rating = None
        review_count = 0
        opiniones_lista = []
        if local.opiniones:
            # Filtrar opiniones no eliminadas
            opiniones_activas = [
                op for op in local.opiniones if op.eliminado_el is None
            ]
            puntuaciones = [
                float(op.puntuacion)
                for op in opiniones_activas
                if op.puntuacion is not None
            ]
            if puntuaciones:
                rating = round(sum(puntuaciones) / len(puntuaciones), 1)
                review_count = len(puntuaciones)

            # Formatear opiniones para respuesta
            for opinion in opiniones_activas:
                opiniones_lista.append(
                    {
                        "id": opinion.id,
                        "usuario": opinion.usuario.nombre
                        if opinion.usuario
                        else "Anonimo",
                        "puntuacion": float(opinion.puntuacion)
                        if opinion.puntuacion
                        else None,
                        "comentario": opinion.comentario,
                        "fecha": opinion.creado_el.isoformat()
                        if opinion.creado_el
                        else None,
                    }
                )

        # Determinar estado (abierto/cerrado)
        status = "closed"
        closing_time = None
        now = datetime.now()
        current_time = now.time()
        current_day = now.weekday() + 1  # 1 = Lunes, 7 = Domingo

        dias_semana = {
            1: "Lunes",
            2: "Martes",
            3: "Miércoles",
            4: "Jueves",
            5: "Viernes",
            6: "Sabado",
            7: "Domingo",
        }

        horarios_formateados = []
        for horario in local.horarios:
            if horario.dia_semana == current_day and horario.abierto:
                # Manejar horarios que cruzan medianoche (ej: 18:00 - 02:00)
                if horario.hora_apertura <= horario.hora_cierre:
                    # Horario normal (no cruza medianoche)
                    if horario.hora_apertura <= current_time <= horario.hora_cierre:
                        status = "open"
                        closing_time = horario.hora_cierre.strftime("%H:%M")
                # Horario que cruza medianoche
                elif (
                    current_time >= horario.hora_apertura
                    or current_time <= horario.hora_cierre
                ):
                    status = "open"
                    closing_time = horario.hora_cierre.strftime("%H:%M")

            horarios_formateados.append(
                {
                    "dia": dias_semana.get(
                        horario.dia_semana, f"Dia {horario.dia_semana}"
                    ),
                    "diaNumero": horario.dia_semana,
                    "apertura": horario.hora_apertura.strftime("%H:%M"),
                    "cierre": horario.hora_cierre.strftime("%H:%M"),
                    "abierto": horario.abierto,
                    "tipo": horario.tipo.value if horario.tipo else "normal",
                }
            )

        # Ordenar horarios por dia
        horarios_formateados.sort(key=lambda x: x["diaNumero"])

        # Obtener todas las fotos organizadas por tipo
        fotos_dict = {
            "banner": [],
            "capturas": [],
            "hero": [],  # Mantener vacio por compatibilidad
            "logo": None,
            "galeria": [],
            "todas": [],
        }

        if local.fotos:
            for foto in local.fotos:
                foto_ruta = add_base64_prefix(foto.data) if foto.data else foto.ruta
                # pyrefly: ignore [missing-attribute]
                fotos_dict["todas"].append(foto_ruta)
                if foto.tipo_foto:
                    tipo_nombre = foto.tipo_foto.nombre.lower()

                    if tipo_nombre == "banner":
                        # pyrefly: ignore [missing-attribute]
                        fotos_dict["banner"].append(foto_ruta)
                    elif tipo_nombre == "capturas":
                        # pyrefly: ignore [missing-attribute]
                        fotos_dict["capturas"].append(foto_ruta)
                        # pyrefly: ignore [missing-attribute]
                        fotos_dict["galeria"].append(
                            foto_ruta
                        )  # Mapear capturas a galeria

        # Intentar asignar logo si hay capturas (fallback)
        if fotos_dict["capturas"]:
            fotos_dict["logo"] = fotos_dict["capturas"][0]

        # Obtener redes sociales
        redes_sociales = []
        if local.redes:
            for red in local.redes:
                redes_sociales.append(
                    {
                        "tipo": red.tipo_red.nombre if red.tipo_red else "Red Social",
                        "usuario": red.nombre_usuario,
                        "url": red.url,
                    }
                )

        # Construir respuesta detallada
        local_data = {
            "id": str(local.id),
            "name": local.nombre,
            "description": local.descripcion,
            "type": local.tipo_local.nombre if local.tipo_local else "Restaurante",
            "address": f"{local.direccion.calle} {local.direccion.numero}"
            if local.direccion and local.direccion.calle
            else "",
            "commune": local.direccion.comuna.nombre
            if local.direccion and local.direccion.comuna
            else "",
            "phone": f"+56{local.telefono}",
            "email": local.correo,
            "images": fotos_dict,
            "rating": rating,
            "reviewCount": review_count,
            "reviews": opiniones_lista,
            "status": status,
            "closingTime": closing_time,
            "coordinates": [
                float(local.direccion.longitud) if local.direccion else -70.6693,
                float(local.direccion.latitud) if local.direccion else -33.4489,
            ],
            "horarios": horarios_formateados,
            "redesSociales": redes_sociales,
        }

        return jsonify(local_data), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@locales_bp.route("/<int:id>/productos", methods=["GET"])
def obtener_productos_local(id):
    """Obtiene el menú de productos de un local agrupados por categoria."""
    try:
        # Verificar que el local existe
        local = db_session.query(Local).filter(Local.id == id).first()
        if not local:
            return jsonify({"error": "Local no encontrado"}), 404

        # Obtener productos del local con categoria
        productos = (
            db_session.query(Producto)
            .options(
                # pyrefly: ignore  # bad-argument-type
                joinedload(Producto.categoria),
                # pyrefly: ignore  # bad-argument-type
                joinedload(Producto.fotos).joinedload(Foto.tipo_foto),
            )
            .filter(Producto.id_local == id)
            .all()
        )

        # Agrupar productos por categoria
        categorias_dict = {}
        for producto in productos:
            categoria_nombre = (
                producto.categoria.nombre if producto.categoria else "Sin Categoria"
            )

            if categoria_nombre not in categorias_dict:
                categorias_dict[categoria_nombre] = {
                    "id": str(producto.categoria.id) if producto.categoria else "0",
                    "nombre": categoria_nombre,
                    "productos": [],
                }

            # Obtener imagen del producto
            imagen = None
            if producto.fotos:
                p_foto = producto.fotos[0]
                imagen = add_base64_prefix(p_foto.data) if p_foto.data else p_foto.ruta

            categorias_dict[categoria_nombre]["productos"].append(
                {
                    "id": str(producto.id),
                    "nombre": producto.nombre,
                    "descripcion": producto.descripcion,
                    "precio": producto.precio,
                    "estado": producto.estado.value
                    if producto.estado
                    else "disponible",
                    "imagen": imagen,
                }
            )

        # Convertir a lista
        categorias_lista = list(categorias_dict.values())

        return jsonify(
            {
                "localId": str(id),
                "localNombre": local.nombre,
                "categorias": categorias_lista,
            }
        ), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@locales_bp.route("/<int:id>/opiniones", methods=["GET"])
def obtener_opiniones_local(id):
    """Obtiene opiniones de un local con paginacion."""
    try:
        # Verificar que el local existe
        local = db_session.query(Local).filter(Local.id == id).first()
        if not local:
            return jsonify({"error": "Local no encontrado"}), 404

        # Parametros de paginacion
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 10, type=int)

        # Validar parametros
        page = max(page, 1)
        if limit < 1 or limit > 50:
            limit = 10

        # Query de opiniones con paginacion
        offset = (page - 1) * limit

        opiniones_query = (
            db_session.query(Opinion)
            # pyrefly: ignore  # bad-argument-type
            .options(joinedload(Opinion.usuario))
            .filter(Opinion.id_local == id, Opinion.eliminado_el.is_(None))
            .order_by(Opinion.creado_el.desc())
        )

        total = opiniones_query.count()
        opiniones = opiniones_query.offset(offset).limit(limit).all()

        # Formatear opiniones
        opiniones_lista = []
        for opinion in opiniones:
            opiniones_lista.append(
                {
                    "id": opinion.id,
                    "usuario": opinion.usuario.nombre if opinion.usuario else "Anonimo",
                    "usuarioId": str(opinion.id_usuario)
                    if opinion.id_usuario
                    else None,
                    # pyrefly: ignore [bad-argument-type]
                    "puntuacion": float(opinion.puntuacion)
                    if opinion.puntuacion
                    else None,
                    "comentario": opinion.comentario,
                    "fecha": opinion.creado_el.isoformat()
                    if opinion.creado_el
                    else None,
                }
            )

        return jsonify(
            {
                "opiniones": opiniones_lista,
                "total": total,
                "page": page,
                "limit": limit,
                "totalPages": (total + limit - 1) // limit,
            }
        ), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@locales_bp.route("/<int:id>/mesas", methods=["GET"])
def obtener_mesas_local(id):
    """Obtiene las mesas de un local."""
    try:
        # Verificar que el local existe
        local = db_session.query(Local).filter(Local.id == id).first()
        if not local:
            return jsonify({"error": "Local no encontrado"}), 404

        # Obtener mesas del local
        mesas = (
            db_session.query(Mesa)
            .filter(Mesa.id_local == id)
            .order_by(Mesa.nombre)
            .all()
        )

        # Formatear mesas
        mesas_lista = []
        for mesa in mesas:
            mesas_lista.append(
                {
                    "id": str(mesa.id),
                    "nombre": mesa.nombre,
                    "descripcion": mesa.descripcion,
                    "capacidad": mesa.capacidad,
                    "estado": mesa.estado.value if mesa.estado else "disponible",
                }
            )

        return jsonify({"localId": str(id), "mesas": mesas_lista}), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@locales_bp.route("/<int:id>/reservas", methods=["GET"])
def obtener_reservas_local(id):
    """Obtiene las reservas de un local para una fecha especifica."""
    try:
        # Verificar que el local existe
        local = db_session.query(Local).filter(Local.id == id).first()
        if not local:
            return jsonify({"error": "Local no encontrado"}), 404

        # Parametro de fecha (formato: YYYY-MM-DD)
        fecha_str = request.args.get("fecha")
        if not fecha_str:
            return jsonify(
                {"error": "Parametro 'fecha' es requerido (formato: YYYY-MM-DD)"}
            ), 400

        try:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Formato de fecha invalido. Use: YYYY-MM-DD"}), 400

        # Obtener reservas del local para esa fecha
        reservas = (
            db_session.query(Reserva)
            # pyrefly: ignore  # bad-argument-type
            .options(joinedload(Reserva.reservas_mesa).joinedload(ReservaMesa.mesa))
            .filter(
                Reserva.id_local == id,
                Reserva.fecha_reserva == fecha,
                Reserva.estado.in_(["pendiente", "confirmada"]),
            )
            .all()
        )

        # Formatear reservas con mesas ocupadas
        reservas_lista = []
        for reserva in reservas:
            for reserva_mesa in reserva.reservas_mesa:
                reservas_lista.append(
                    {
                        "id": reserva.id,
                        "mesaId": str(reserva_mesa.mesa.id),
                        "mesaNombre": reserva_mesa.mesa.nombre,
                        "horaReserva": reserva.hora_reserva.strftime("%H:%M")
                        if reserva.hora_reserva
                        else None,
                        "estado": reserva.estado.value,
                    }
                )

        return jsonify(
            {"localId": str(id), "fecha": fecha_str, "reservas": reservas_lista}
        ), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@locales_bp.route("/<int:id>/horarios-disponibles", methods=["GET"])
def obtener_horarios_disponibles(id):
    """
    Obtiene los horarios disponibles de un local para una fecha especifica.
    Si es el mismo dia, retorna horarios con minimo 2 horas desde la hora actual.
    """
    try:
        # Verificar que el local existe
        local = (
            db_session.query(Local)
            # pyrefly: ignore  # bad-argument-type
            .options(joinedload(Local.horarios))
            .filter(Local.id == id)
            .first()
        )

        if not local:
            return jsonify({"error": "Local no encontrado"}), 404

        # Parametro de fecha (formato: YYYY-MM-DD)
        fecha_str = request.args.get("fecha")
        if not fecha_str:
            return jsonify(
                {"error": "Parametro 'fecha' es requerido (formato: YYYY-MM-DD)"}
            ), 400

        try:
            fecha_seleccionada = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Formato de fecha invalido. Use: YYYY-MM-DD"}), 400

        # Obtener el dia de la semana (1=Lunes, 7=Domingo)
        dia_semana = fecha_seleccionada.isoweekday()

        # Buscar horario del local para ese dia
        horario = next(
            (h for h in local.horarios if h.dia_semana == dia_semana and h.abierto),
            None,
        )

        if not horario:
            return jsonify(
                {
                    "localId": str(id),
                    "fecha": fecha_str,
                    "horarios": [],
                    "mensaje": "El local esta cerrado este dia",
                }
            ), 200

        # Generar slots de tiempo cada 15 minutos desde apertura hasta 1 hora antes del cierre
        def generar_slots(hora_inicio: time, hora_fin: time):
            slots = []
            hora_actual = datetime.combine(fecha_seleccionada, hora_inicio)
            hora_final = datetime.combine(fecha_seleccionada, hora_fin)

            # Restar 1 hora al cierre para última reserva
            hora_final = hora_final - timedelta(hours=1)

            while hora_actual < hora_final:
                slots.append(hora_actual.strftime("%H:%M"))
                hora_actual += timedelta(minutes=15)

            return slots

        slots_disponibles = generar_slots(horario.hora_apertura, horario.hora_cierre)

        # Si es el mismo dia, filtrar horarios que sean al menos 2 horas desde ahora
        ahora = datetime.now()
        if fecha_seleccionada == ahora.date():
            hora_minima = (ahora + timedelta(hours=2)).time()
            slots_disponibles = [
                slot
                for slot in slots_disponibles
                if datetime.strptime(slot, "%H:%M").time() >= hora_minima
            ]

        return jsonify(
            {"localId": str(id), "fecha": fecha_str, "horarios": slots_disponibles}
        ), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@locales_bp.route("/<int:id>/mesas-disponibles", methods=["GET"])
def obtener_mesas_disponibles(id):
    """
    Verifica la disponibilidad de mesas para una fecha y hora especifica.
    """
    try:
        # Verificar que el local existe
        local = db_session.query(Local).filter(Local.id == id).first()
        if not local:
            return jsonify({"error": "Local no encontrado"}), 404

        # Parametros requeridos
        fecha_str = request.args.get("fecha")
        hora_str = request.args.get("hora")

        if not fecha_str or not hora_str:
            return jsonify({"error": "Parametros 'fecha' y 'hora' son requeridos"}), 400

        try:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            hora = datetime.strptime(hora_str, "%H:%M").time()
        except ValueError:
            return jsonify({"error": "Formato de fecha u hora invalido"}), 400

        # Obtener todas las mesas del local
        mesas = (
            db_session.query(Mesa)
            .filter(Mesa.id_local == id)
            .order_by(Mesa.nombre)
            .all()
        )

        # Verificar disponibilidad de cada mesa
        # Considerar un rango de ±75 minutos (1 hora y 15 minutos)
        hora_inicio = (datetime.combine(fecha, hora) - timedelta(minutes=75)).time()
        hora_fin = (datetime.combine(fecha, hora) + timedelta(minutes=75)).time()

        # Obtener IDs de mesas ocupadas en ese rango
        mesas_ocupadas = (
            db_session.query(ReservaMesa.id_mesa)
            .join(Reserva)
            .filter(
                Reserva.id_local == id,
                Reserva.fecha_reserva == fecha,
                Reserva.hora_reserva >= hora_inicio,
                Reserva.hora_reserva <= hora_fin,
                Reserva.estado.in_(["pendiente", "confirmada"]),
            )
            .distinct()
            .all()
        )

        mesas_ocupadas_ids = {mesa_id for (mesa_id,) in mesas_ocupadas}

        # Formatear respuesta con estado de disponibilidad
        mesas_lista = []
        for mesa in mesas:
            esta_disponible = mesa.id not in mesas_ocupadas_ids
            mesas_lista.append(
                {
                    "id": str(mesa.id),
                    "nombre": mesa.nombre,
                    "descripcion": mesa.descripcion,
                    "capacidad": mesa.capacidad,
                    "estado": "disponible" if esta_disponible else "reservada",
                }
            )

        return jsonify(
            {
                "localId": str(id),
                "fecha": fecha_str,
                "hora": hora_str,
                "mesas": mesas_lista,
            }
        ), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@locales_bp.route("/<int:id>/verificar-reserva-activa", methods=["GET"])
def verificar_reserva_activa(id):
    """
    Verifica si el usuario autenticado tiene una reserva activa en este local.
    Requiere autenticación.
    """
    try:
        from utils.jwt_helper import verificar_token

        # Obtener token del header Authorization
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            # Si no hay token, retornar que no hay reserva (usuario no autenticado)
            return jsonify({"tieneReservaActiva": False}), 200

        # Verificar formato "Bearer {token}"
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({"tieneReservaActiva": False}), 200

        token = parts[1]
        payload = verificar_token(token)
        if not payload:
            return jsonify({"tieneReservaActiva": False}), 200

        user_id = payload["user_id"]

        # Verificar que el local existe
        local = db_session.query(Local).filter(Local.id == id).first()
        if not local:
            return jsonify({"error": "Local no encontrado"}), 404

        # Buscar reserva activa del usuario en este local
        reserva_activa = (
            db_session.query(Reserva)
            .filter(
                Reserva.id_usuario == user_id,
                Reserva.id_local == id,
                Reserva.estado == "pendiente",
            )
            .first()
        )

        if reserva_activa:
            # Obtener código QR activo
            qr_codigo = None
            qr_base64 = None
            if reserva_activa.qr_dinamicos:
                # Buscar el QR más reciente o activo
                qr = next((q for q in reserva_activa.qr_dinamicos if q.activo), None)
                if qr:
                    qr_codigo = qr.codigo
                    # Generar imagen QR
                    import json

                    from services.qr_service import generar_qr_imagen

                    # Obtener mesa de la reserva
                    mesa_id = None
                    if reserva_activa.reservas_mesa:
                        mesa_id = reserva_activa.reservas_mesa[0].id_mesa

                    try:
                        qr_data = {
                            "tipo": "reserva",
                            "codigo": qr_codigo,
                            "reserva_id": reserva_activa.id,
                            "mesa_id": mesa_id,
                            "local_id": reserva_activa.id_local,
                            "fecha": reserva_activa.fecha_reserva.isoformat()
                            if reserva_activa.fecha_reserva
                            else None,
                            "hora": reserva_activa.hora_reserva.strftime("%H:%M")
                            if reserva_activa.hora_reserva
                            else None,
                        }
                        qr_string = json.dumps(qr_data)
                        qr_base64 = generar_qr_imagen(qr_string)
                    except Exception as e:
                        print(
                            f"Error generando QR para reserva {reserva_activa.id}: {e}"
                        )

            return jsonify(
                {
                    "tieneReservaActiva": True,
                    "reserva": {
                        "id": reserva_activa.id,
                        "fecha": reserva_activa.fecha_reserva.strftime("%Y-%m-%d")
                        if reserva_activa.fecha_reserva
                        else None,
                        "hora": reserva_activa.hora_reserva.strftime("%H:%M")
                        if reserva_activa.hora_reserva
                        else None,
                        "estado": reserva_activa.estado.value
                        if reserva_activa.estado
                        else "pendiente",
                        "codigoQR": qr_codigo or f"RES-{reserva_activa.id}",
                        "qrImage": qr_base64,
                    },
                }
            ), 200
        else:
            return jsonify({"tieneReservaActiva": False}), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ============================================
# ENDPOINTS PUT - Actualización de Local
# ============================================


@locales_bp.route("/<int:local_id>/info", methods=["PUT"])
def actualizar_info_local(local_id):
    """Actualiza la información básica del local (nombre, teléfono, correo)."""
    try:
        local = db_session.query(Local).get(local_id)
        if not local:
            return jsonify({"error": "Local no encontrado"}), 404

        data = request.get_json()
        if not data:
            return jsonify({"error": "No se proporcionaron datos"}), 400

        # Campos editables
        if "nombre" in data:
            local.nombre = data["nombre"]
        if "telefono" in data:
            local.telefono = data["telefono"]
        if "descripcion" in data:
            local.descripcion = data["descripcion"]
        if "correo" in data:
            # Verificar que el correo no esté en uso por otro local
            existing = (
                db_session.query(Local)
                .filter(Local.correo == data["correo"], Local.id != local_id)
                .first()
            )
            if existing:
                return jsonify({"error": "El correo ya está en uso"}), 400
            local.correo = data["correo"]

        db_session.commit()
        return jsonify(
            {
                "message": "Información actualizada correctamente",
                "local": {
                    "id": local.id,
                    "nombre": local.nombre,
                    "telefono": local.telefono,
                    "correo": local.correo,
                },
            }
        ), 200

    except Exception as e:
        db_session.rollback()
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@locales_bp.route("/<int:local_id>/horarios", methods=["PUT"])
def actualizar_horarios_local(local_id):
    """Actualiza los horarios del local."""
    from models import Horario

    try:
        local = db_session.query(Local).get(local_id)
        if not local:
            return jsonify({"error": "Local no encontrado"}), 404

        data = request.get_json()
        if not data or "horarios" not in data:
            return jsonify({"error": "No se proporcionaron horarios"}), 400

        # Eliminar horarios existentes
        db_session.query(Horario).filter(Horario.id_local == local_id).delete()

        # Crear nuevos horarios
        from datetime import date as date_module

        from models import TipoHorarioEnum

        for h in data["horarios"]:
            horario = Horario(
                id_local=local_id,
                tipo=TipoHorarioEnum.NORMAL,
                fecha_inicio=date_module.today(),
                fecha_fin=date_module(2099, 12, 31),  # Fecha lejana como "sin fin"
                dia_semana=h["dia_semana"],
                hora_apertura=time.fromisoformat(h["hora_apertura"])
                if h.get("hora_apertura")
                else time(9, 0),
                hora_cierre=time.fromisoformat(h["hora_cierre"])
                if h.get("hora_cierre")
                else time(22, 0),
                abierto=h.get("abierto", True),
            )
            db_session.add(horario)

        db_session.commit()
        return jsonify({"message": "Horarios actualizados correctamente"}), 200

    except Exception as e:
        db_session.rollback()
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@locales_bp.route("/<int:local_id>/redes", methods=["PUT"])
def actualizar_redes_local(local_id):
    """Actualiza las redes sociales del local."""
    try:
        local = db_session.query(Local).get(local_id)
        if not local:
            return jsonify({"error": "Local no encontrado"}), 404

        data = request.get_json()
        if not data or "redes" not in data:
            return jsonify({"error": "No se proporcionaron redes sociales"}), 400

        # Eliminar redes existentes
        db_session.query(Redes).filter(Redes.id_local == local_id).delete()

        # Crear nuevas redes
        for r in data["redes"]:
            red = Redes(
                id_local=local_id,
                id_tipo_red=r["id_tipo_red"],
                url=r["url"],
            )
            db_session.add(red)

        db_session.commit()
        return jsonify({"message": "Redes sociales actualizadas correctamente"}), 200

    except Exception as e:
        db_session.rollback()
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
