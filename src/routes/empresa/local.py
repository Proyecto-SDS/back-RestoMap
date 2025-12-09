"""
Rutas para información del local de empresa
Prefix: /api/empresa/local/*
"""

from flask import Blueprint, jsonify, request
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from database import get_session
from models import Direccion, Local, Redes, TipoRed
from utils.jwt_helper import verificar_token

# URLs base para cada tipo de red social
SOCIAL_URLS = {
    "Instagram": "https://instagram.com/",
    "Facebook": "https://facebook.com/",
    "TikTok": "https://tiktok.com/@",
    "YouTube": "https://youtube.com/@",
    "X/Twitter": "https://x.com/",
    "WhatsApp": "https://wa.me/",
    "LinkedIn": "https://linkedin.com/in/",
    "Sitio Web": "",  # URL completa proporcionada por el usuario
}


def generar_url_red(tipo_nombre: str, nombre_usuario: str) -> str:
    """Genera la URL completa para una red social dado el tipo y nombre de usuario."""
    if not nombre_usuario:
        return ""

    # Limpiar el nombre de usuario (quitar @ si viene)
    nombre_limpio = nombre_usuario.lstrip("@").strip()

    # Para WhatsApp, limpiar todo excepto números y el +
    if tipo_nombre == "WhatsApp":
        nombre_limpio = "".join(c for c in nombre_usuario if c.isdigit() or c == "+")

    # Para Sitio Web, devolver tal cual si ya tiene protocolo
    if tipo_nombre == "Sitio Web":
        if nombre_usuario.startswith(("http://", "https://")):
            return nombre_usuario
        return f"https://{nombre_usuario}"

    base_url = SOCIAL_URLS.get(tipo_nombre, "")
    if not base_url:
        return nombre_usuario  # Fallback

    return f"{base_url}{nombre_limpio}"


local_bp = Blueprint("local", __name__, url_prefix="/local")


@local_bp.route("/tipos-red", methods=["GET"])
def obtener_tipos_red():
    """Obtiene todos los tipos de redes sociales disponibles."""
    db = get_session()
    try:
        tipos = db.execute(select(TipoRed).order_by(TipoRed.nombre)).scalars().all()
        return jsonify([{"id": t.id, "nombre": t.nombre} for t in tipos]), 200
    finally:
        db.close()


@local_bp.route("/redes", methods=["PUT"])
def actualizar_redes():
    """Actualiza las redes sociales del local."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Token no proporcionado"}), 401

    token = auth_header.split(" ")[1]
    payload = verificar_token(token)
    if not payload:
        return jsonify({"error": "Token inválido"}), 401

    id_local = payload.get("id_local")
    if not id_local:
        return jsonify({"error": "Usuario no asociado a un local"}), 403

    data = request.get_json()
    # data debe ser lista de { id_tipo_red: int, nombre_usuario: string }

    db = get_session()
    try:
        # Verificar que el local existe
        local = db.execute(
            select(Local).where(Local.id == id_local)
        ).scalar_one_or_none()
        if not local:
            return jsonify({"error": "Local no encontrado"}), 404

        # Eliminar redes actuales
        db.query(Redes).filter(Redes.id_local == id_local).delete()

        # Insertar nuevas redes
        if data and isinstance(data, list):
            for item in data:
                nombre_usuario = item.get("nombre_usuario", "").strip()
                id_tipo = item.get("id_tipo_red")

                if nombre_usuario and id_tipo:
                    # Obtener el tipo de red para generar la URL
                    tipo_red = db.execute(
                        select(TipoRed).where(TipoRed.id == id_tipo)
                    ).scalar_one_or_none()

                    tipo_nombre = tipo_red.nombre if tipo_red else ""
                    url_generada = generar_url_red(tipo_nombre, nombre_usuario)

                    # Limpiar @ del nombre para guardarlo limpio
                    nombre_limpio = nombre_usuario.lstrip("@").strip()

                    nueva_red = Redes(
                        id_local=id_local,
                        id_tipo_red=id_tipo,
                        nombre_usuario=nombre_limpio,
                        url=url_generada,
                    )
                    db.add(nueva_red)

        db.commit()
        return jsonify({"message": "Redes actualizadas correctamente"}), 200

    except Exception as e:
        db.rollback()
        print(f"Error actualizando redes: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@local_bp.route("/", methods=["GET"])
def obtener_local_info():
    """Obtiene la información del local del empleado autenticado."""
    # Obtener usuario del token
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Token no proporcionado"}), 401

    token = auth_header.split(" ")[1]
    payload = verificar_token(token)
    if not payload:
        return jsonify({"error": "Token inválido"}), 401

    id_local = payload.get("id_local")
    if not id_local:
        return jsonify({"error": "Usuario no asociado a un local"}), 403

    db = get_session()
    try:
        stmt = (
            select(Local)
            .options(
                joinedload(Local.direccion).joinedload(Direccion.comuna),
                joinedload(Local.tipo_local),
                joinedload(Local.horarios),
                joinedload(Local.redes),
            )
            .where(Local.id == id_local)
        )
        local = db.execute(stmt).unique().scalar_one_or_none()

        if not local:
            return jsonify({"error": "Local no encontrado"}), 404

        # Formatear horarios
        horarios = []
        for h in local.horarios:
            horarios.append(
                {
                    "dia_semana": h.dia_semana,
                    "hora_apertura": h.hora_apertura.strftime("%H:%M")
                    if h.hora_apertura
                    else None,
                    "hora_cierre": h.hora_cierre.strftime("%H:%M")
                    if h.hora_cierre
                    else None,
                    "abierto": h.abierto,
                }
            )

        # Formatear redes
        redes = []
        for r in local.redes:
            redes.append(
                {
                    "id_tipo_red": r.id_tipo_red,
                    "nombre_usuario": r.nombre_usuario,
                }
            )

        return jsonify(
            {
                "id": local.id,
                "nombre": local.nombre,
                "descripcion": local.descripcion,
                "telefono": local.telefono,
                "correo": local.correo,
                "tipo_local": local.tipo_local.nombre if local.tipo_local else None,
                "direccion": {
                    "calle": local.direccion.calle if local.direccion else None,
                    "numero": local.direccion.numero if local.direccion else None,
                    "comuna": local.direccion.comuna.nombre
                    if local.direccion and local.direccion.comuna
                    else None,
                }
                if local.direccion
                else None,
                "horarios": horarios,
                "redes": redes,
            }
        ), 200

    finally:
        db.close()
