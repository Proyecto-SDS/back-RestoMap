"""
Rutas para gestión de fotos del local de empresa
Prefix: /api/empresa/fotos/*

Las imágenes se almacenan en la base de datos como base64
para compatibilidad con Cloud Run (sin sistema de archivos persistente)
"""

from flask import Blueprint, jsonify, request
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from database import get_session
from models import Foto, Producto, TipoFoto
from utils.jwt_helper import verificar_token

fotos_bp = Blueprint("fotos", __name__, url_prefix="/fotos")

# Configuración
MAX_FOTOS_CAPTURAS = 15
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


def allowed_file(filename):
    """Verifica si el archivo tiene una extensión permitida"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def normalize_base64(base64_string):
    """
    Normaliza una cadena base64, removiendo el prefijo data:image si existe
    y asegurando que tenga el formato correcto para almacenar
    """
    try:
        # Remover el prefijo data:image/...;base64, si existe
        if "," in base64_string:
            base64_string = base64_string.split(",")[1]

        # Validar que sea base64 válido
        # Si no tiene el prefijo, lo agregamos para servir
        return base64_string.strip()
    except Exception as e:
        print(f"Error normalizando base64: {e}")
        return None


def add_base64_prefix(data):
    """
    Agrega el prefijo data:image/...;base64, necesario para que el navegador
    interprete la imagen correctamente si solo tenemos el string base64.
    """
    if not data:
        return None

    if data.startswith("data:"):
        return data

    # Detección simple basada en firmas mágicas
    if data.startswith("/9j/"):
        mime = "jpeg"
    elif data.startswith("iVBORw"):
        mime = "png"
    elif data.startswith("UklGR"):
        mime = "webp"
    else:
        mime = "jpeg"  # Fallback

    return f"data:image/{mime};base64,{data}"


@fotos_bp.route("/", methods=["GET"])
def obtener_fotos():
    """Obtiene todas las fotos del local del empleado autenticado."""
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
            select(Foto)
            .options(joinedload(Foto.tipo_foto))
            .where(Foto.id_local == id_local)
        )
        fotos = db.execute(stmt).unique().scalars().all()

        # Organizar fotos por tipo
        banner_foto = None
        capturas_fotos = []

        for foto in fotos:
            # Retornar la imagen como data URI para que se muestre directamente
            # Si tiene data (base64), reconstruir prefijo; si tiene ruta (legacy), mantenerla
            foto_ruta = add_base64_prefix(foto.data) if foto.data else foto.ruta

            foto_data = {
                "id": foto.id,
                "ruta": foto_ruta,
                "tipo": foto.tipo_foto.nombre if foto.tipo_foto else None,
            }

            if foto.tipo_foto and foto.tipo_foto.nombre == "banner":
                banner_foto = foto_data
            elif foto.tipo_foto and foto.tipo_foto.nombre == "capturas":
                capturas_fotos.append(foto_data)

        resultado = {"banner": banner_foto, "capturas": capturas_fotos}

        return jsonify(resultado), 200

    finally:
        db.close()


@fotos_bp.route("/banner", methods=["POST"])
def actualizar_banner():
    """Actualiza o crea la imagen banner del local (solo puede haber 1)."""
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

    data = request.get_json()
    if not data or "imagen" not in data:
        return jsonify({"error": "No se proporcionó imagen"}), 400

    db = get_session()
    try:
        # Obtener tipo_foto banner (id=1)
        tipo_banner = db.execute(
            select(TipoFoto).where(TipoFoto.nombre == "banner")
        ).scalar_one_or_none()

        if not tipo_banner:
            return jsonify({"error": "Tipo de foto banner no encontrado"}), 500

        # Normalizar la imagen base64
        base64_data = normalize_base64(data["imagen"])

        if not base64_data:
            return jsonify({"error": "Formato de imagen inválido"}), 400

        # Buscar si ya existe un banner
        banner_existente = db.execute(
            select(Foto).where(
                Foto.id_local == id_local, Foto.id_tipo_foto == tipo_banner.id
            )
        ).scalar_one_or_none()

        if banner_existente:
            # Actualizar con nueva imagen
            banner_existente.data = base64_data
            banner_existente.ruta = None  # Limpiar ruta antigua si existe
        else:
            # Crear nuevo banner
            nuevo_banner = Foto(
                id_local=id_local,
                id_tipo_foto=tipo_banner.id,
                data=base64_data,
                ruta=None,
            )
            db.add(nuevo_banner)

        db.commit()

        return jsonify({"message": "Banner actualizado correctamente"}), 200

    except Exception as e:
        db.rollback()
        print(f"Error actualizando banner: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@fotos_bp.route("/capturas", methods=["POST"])
def agregar_captura():
    """Agrega una nueva foto de captura (máximo 15)."""
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

    data = request.get_json()
    if not data or "imagen" not in data:
        return jsonify({"error": "No se proporcionó imagen"}), 400

    db = get_session()
    try:
        # Obtener tipo_foto capturas (id=2)
        tipo_capturas = db.execute(
            select(TipoFoto).where(TipoFoto.nombre == "capturas")
        ).scalar_one_or_none()

        if not tipo_capturas:
            return jsonify({"error": "Tipo de foto capturas no encontrado"}), 500

        # Verificar cantidad de capturas existentes
        count = (
            db.execute(
                select(Foto).where(
                    Foto.id_local == id_local, Foto.id_tipo_foto == tipo_capturas.id
                )
            )
            .scalars()
            .all()
        )

        if len(count) >= MAX_FOTOS_CAPTURAS:
            return (
                jsonify({"error": f"Máximo {MAX_FOTOS_CAPTURAS} fotos permitidas"}),
                400,
            )

        # Normalizar la imagen base64
        base64_data = normalize_base64(data["imagen"])

        if not base64_data:
            return jsonify({"error": "Formato de imagen inválido"}), 400

        # Crear nueva captura
        nueva_captura = Foto(
            id_local=id_local,
            id_tipo_foto=tipo_capturas.id,
            data=base64_data,
            ruta=None,
        )
        db.add(nueva_captura)
        db.commit()

        return (
            jsonify(
                {
                    "message": "Foto agregada correctamente",
                    "id": nueva_captura.id,
                }
            ),
            201,
        )

    except Exception as e:
        db.rollback()
        print(f"Error agregando captura: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@fotos_bp.route("/capturas/<int:foto_id>", methods=["DELETE"])
def eliminar_captura(foto_id):
    """Elimina una foto de captura específica."""
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
        # Buscar la foto
        foto = db.execute(
            select(Foto).where(Foto.id == foto_id, Foto.id_local == id_local)
        ).scalar_one_or_none()

        if not foto:
            return jsonify({"error": "Foto no encontrada"}), 404

        # Verificar que sea una captura (no banner)
        tipo_capturas = db.execute(
            select(TipoFoto).where(TipoFoto.nombre == "capturas")
        ).scalar_one_or_none()

        if foto.id_tipo_foto != tipo_capturas.id:
            return jsonify({"error": "Solo se pueden eliminar fotos de capturas"}), 400

        # Eliminar registro de BD (la imagen está en el campo data, se elimina automáticamente)
        db.delete(foto)
        db.commit()

        return jsonify({"message": "Foto eliminada correctamente"}), 200

    except Exception as e:
        db.rollback()
        print(f"Error eliminando captura: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


# ============================================
# FOTOS DE PRODUCTOS
# ============================================


@fotos_bp.route("/producto/<int:producto_id>", methods=["GET"])
def obtener_foto_producto(producto_id):
    """Obtiene la foto de un producto."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Token no proporcionado"}), 401

    token = auth_header.split(" ")[1]
    payload = verificar_token(token)
    if not payload:
        return jsonify({"error": "Token invalido"}), 401

    id_local = payload.get("id_local")
    if not id_local:
        return jsonify({"error": "Usuario no asociado a un local"}), 403

    db = get_session()
    try:
        # Verificar que el producto pertenece al local
        producto = db.execute(
            select(Producto).where(
                Producto.id == producto_id, Producto.id_local == id_local
            )
        ).scalar_one_or_none()

        if not producto:
            return jsonify({"error": "Producto no encontrado"}), 404

        # Buscar foto del producto
        foto = db.execute(
            select(Foto).where(Foto.id_producto == producto_id)
        ).scalar_one_or_none()

        if not foto:
            return jsonify({"foto": None}), 200

        foto_ruta = add_base64_prefix(foto.data) if foto.data else foto.ruta

        return jsonify({"foto": {"id": foto.id, "ruta": foto_ruta}}), 200

    finally:
        db.close()


@fotos_bp.route("/producto/<int:producto_id>", methods=["POST"])
def actualizar_foto_producto(producto_id):
    """Actualiza o crea la foto de un producto (solo puede haber 1 por producto)."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Token no proporcionado"}), 401

    token = auth_header.split(" ")[1]
    payload = verificar_token(token)
    if not payload:
        return jsonify({"error": "Token invalido"}), 401

    id_local = payload.get("id_local")
    if not id_local:
        return jsonify({"error": "Usuario no asociado a un local"}), 403

    data = request.get_json()
    if not data or "imagen" not in data:
        return jsonify({"error": "No se proporciono imagen"}), 400

    db = get_session()
    try:
        # Verificar que el producto pertenece al local
        producto = db.execute(
            select(Producto).where(
                Producto.id == producto_id, Producto.id_local == id_local
            )
        ).scalar_one_or_none()

        if not producto:
            return jsonify({"error": "Producto no encontrado"}), 404

        # Normalizar la imagen base64
        base64_data = normalize_base64(data["imagen"])

        if not base64_data:
            return jsonify({"error": "Formato de imagen invalido"}), 400

        # Buscar si ya existe una foto para este producto
        foto_existente = db.execute(
            select(Foto).where(Foto.id_producto == producto_id)
        ).scalar_one_or_none()

        if foto_existente:
            # Actualizar foto existente
            foto_existente.data = base64_data
            foto_existente.ruta = None
        else:
            # Crear nueva foto
            nueva_foto = Foto(
                id_producto=producto_id,
                id_local=id_local,
                data=base64_data,
                ruta=None,
            )
            db.add(nueva_foto)

        db.commit()

        return jsonify({"message": "Foto de producto actualizada correctamente"}), 200

    except Exception as e:
        db.rollback()
        print(f"Error actualizando foto de producto: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@fotos_bp.route("/producto/<int:producto_id>", methods=["DELETE"])
def eliminar_foto_producto(producto_id):
    """Elimina la foto de un producto."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Token no proporcionado"}), 401

    token = auth_header.split(" ")[1]
    payload = verificar_token(token)
    if not payload:
        return jsonify({"error": "Token invalido"}), 401

    id_local = payload.get("id_local")
    if not id_local:
        return jsonify({"error": "Usuario no asociado a un local"}), 403

    db = get_session()
    try:
        # Verificar que el producto pertenece al local
        producto = db.execute(
            select(Producto).where(
                Producto.id == producto_id, Producto.id_local == id_local
            )
        ).scalar_one_or_none()

        if not producto:
            return jsonify({"error": "Producto no encontrado"}), 404

        # Buscar la foto
        foto = db.execute(
            select(Foto).where(Foto.id_producto == producto_id)
        ).scalar_one_or_none()

        if not foto:
            return jsonify({"error": "Foto no encontrada"}), 404

        db.delete(foto)
        db.commit()

        return jsonify({"message": "Foto de producto eliminada correctamente"}), 200

    except Exception as e:
        db.rollback()
        print(f"Error eliminando foto de producto: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()
