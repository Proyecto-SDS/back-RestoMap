"""
Rutas para gestión de productos del local
Prefix: /api/empresa/productos/*
"""

from flask import Blueprint, jsonify, request
from pydantic import BaseModel, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from database import get_session
from models.models import EstadoProductoEnum, Producto
from routes.empresa import requerir_empleado, requerir_roles_empresa
from utils.jwt_helper import requerir_auth
from websockets import emit_producto_actualizado

productos_bp = Blueprint("productos", __name__, url_prefix="/productos")


# ============================================
# SCHEMAS
# ============================================


class ProductoEstadoSchema(BaseModel):
    estado: EstadoProductoEnum


class ProductoCreateSchema(BaseModel):
    nombre: str
    descripcion: str | None = None
    precio: int
    categoria_id: int | None = None


class ProductoUpdateSchema(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None
    precio: int | None = None
    categoria_id: int | None = None


# ============================================
# ENDPOINTS
# ============================================


@productos_bp.route("/", methods=["GET"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente", "mesero", "cocinero", "bartender")
def listar_productos(user_id, user_rol, id_local):
    """Listar todos los productos del local"""
    categoria_filter = request.args.get("categoria")
    estado_filter = request.args.get("estado")

    db = get_session()
    try:
        stmt = (
            select(Producto)
            .options(joinedload(Producto.categoria))
            .where(Producto.id_local == id_local)
            .order_by(Producto.nombre)
        )

        if categoria_filter:
            stmt = stmt.where(Producto.id_categoria == int(categoria_filter))

        if estado_filter:
            try:
                estado_enum = EstadoProductoEnum(estado_filter)
                stmt = stmt.where(Producto.estado == estado_enum)
            except ValueError:
                pass

        productos = db.execute(stmt).unique().scalars().all()

        result = []
        for producto in productos:
            result.append(
                {
                    "id": producto.id,
                    "nombre": producto.nombre,
                    "descripcion": producto.descripcion,
                    "precio": producto.precio,
                    "estado": producto.estado.value
                    if producto.estado
                    else "disponible",
                    "categoria_id": producto.id_categoria,
                    "categoria_nombre": producto.categoria.nombre
                    if producto.categoria
                    else None,
                }
            )

        return jsonify(result), 200
    finally:
        db.close()


@productos_bp.route("/<int:producto_id>/estado", methods=["PATCH"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente", "cocinero", "bartender")
def cambiar_estado_producto(producto_id, user_id, user_rol, id_local):
    """Cambiar estado de disponibilidad de un producto"""
    try:
        data = ProductoEstadoSchema(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": "Datos inválidos", "details": e.errors()}), 400

    db = get_session()
    try:
        stmt = select(Producto).where(
            Producto.id == producto_id, Producto.id_local == id_local
        )
        producto = db.execute(stmt).scalar_one_or_none()

        if not producto:
            return jsonify({"error": "Producto no encontrado"}), 404

        producto.estado = data.estado
        db.commit()

        # Emitir evento WebSocket
        try:
            emit_producto_actualizado(
                id_local,
                {
                    "id": producto.id,
                    "estado": producto.estado.value,
                    "id_categoria": producto.id_categoria,
                },
            )
        except Exception:
            pass

        return jsonify(
            {
                "message": "Estado del producto actualizado",
                "producto": {
                    "id": producto.id,
                    "nombre": producto.nombre,
                    "estado": producto.estado.value,
                },
            }
        ), 200
    finally:
        db.close()


@productos_bp.route("/", methods=["POST"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente")
def crear_producto(user_id, user_rol, id_local):
    """Crear un nuevo producto"""
    try:
        data = ProductoCreateSchema(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": "Datos invalidos", "details": e.errors()}), 400

    db = get_session()
    try:
        nuevo_producto = Producto(
            id_local=id_local,
            nombre=data.nombre,
            descripcion=data.descripcion,
            precio=data.precio,
            id_categoria=data.categoria_id,
            estado=EstadoProductoEnum.DISPONIBLE,
        )
        db.add(nuevo_producto)
        db.commit()
        db.refresh(nuevo_producto)

        return jsonify(
            {
                "message": "Producto creado exitosamente",
                "producto": {
                    "id": nuevo_producto.id,
                    "nombre": nuevo_producto.nombre,
                    "descripcion": nuevo_producto.descripcion,
                    "precio": nuevo_producto.precio,
                    "estado": nuevo_producto.estado.value,
                    "categoria_id": nuevo_producto.id_categoria,
                },
            }
        ), 201
    finally:
        db.close()


@productos_bp.route("/<int:producto_id>", methods=["PUT"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente")
def actualizar_producto(producto_id, user_id, user_rol, id_local):
    """Actualizar un producto"""
    try:
        data = ProductoUpdateSchema(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": "Datos invalidos", "details": e.errors()}), 400

    db = get_session()
    try:
        stmt = select(Producto).where(
            Producto.id == producto_id, Producto.id_local == id_local
        )
        producto = db.execute(stmt).scalar_one_or_none()

        if not producto:
            return jsonify({"error": "Producto no encontrado"}), 404

        if data.nombre is not None:
            producto.nombre = data.nombre
        if data.descripcion is not None:
            producto.descripcion = data.descripcion
        if data.precio is not None:
            producto.precio = data.precio
        if data.categoria_id is not None:
            producto.id_categoria = data.categoria_id

        db.commit()

        return jsonify(
            {
                "message": "Producto actualizado",
                "producto": {
                    "id": producto.id,
                    "nombre": producto.nombre,
                    "descripcion": producto.descripcion,
                    "precio": producto.precio,
                    "estado": producto.estado.value,
                    "categoria_id": producto.id_categoria,
                },
            }
        ), 200
    finally:
        db.close()


@productos_bp.route("/<int:producto_id>", methods=["DELETE"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente")
def eliminar_producto(producto_id, user_id, user_rol, id_local):
    """Eliminar un producto"""
    db = get_session()
    try:
        stmt = select(Producto).where(
            Producto.id == producto_id, Producto.id_local == id_local
        )
        producto = db.execute(stmt).scalar_one_or_none()

        if not producto:
            return jsonify({"error": "Producto no encontrado"}), 404

        db.delete(producto)
        db.commit()

        return jsonify({"message": "Producto eliminado exitosamente"}), 200
    finally:
        db.close()
