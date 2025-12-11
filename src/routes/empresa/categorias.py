"""
Rutas para gestion de categorias del local
Prefix: /api/empresa/categorias/*
"""

from flask import Blueprint, jsonify, request
from pydantic import BaseModel, ValidationError
from sqlalchemy import func, select

from database import get_session
from models.models import Categoria, Producto, TipoCategoria
from routes.empresa import requerir_empleado, requerir_roles_empresa
from utils.jwt_helper import requerir_auth

categorias_bp = Blueprint("categorias", __name__, url_prefix="/categorias")


# ============================================
# SCHEMAS
# ============================================


class CategoriaCreateSchema(BaseModel):
    nombre: str
    id_tipo_categoria: int  # 1=Comida, 2=Bebida


class CategoriaUpdateSchema(BaseModel):
    nombre: str | None = None
    id_tipo_categoria: int | None = None


# ============================================
# ENDPOINTS
# ============================================


@categorias_bp.route("/", methods=["GET"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente", "mesero", "cocinero", "bartender")
def listar_categorias(user_id, user_rol, id_local):
    """Listar todas las categorias disponibles"""
    tipo_filter = request.args.get("tipo")

    db = get_session()
    try:
        stmt = (
            select(Categoria)
            .where(
                Categoria.id_local == id_local,
                Categoria.eliminado_el.is_(None),
            )
            .order_by(Categoria.nombre)
        )

        if tipo_filter:
            stmt = stmt.where(Categoria.id_tipo_categoria == int(tipo_filter))

        categorias = db.execute(stmt).scalars().all()

        result = []
        for categoria in categorias:
            # Contar productos asociados a esta categoria en el local
            count_stmt = select(func.count(Producto.id)).where(
                Producto.id_categoria == categoria.id,
                Producto.id_local == id_local,
                Producto.eliminado_el.is_(None),
            )
            productos_count = db.execute(count_stmt).scalar() or 0

            result.append(
                {
                    "id": categoria.id,
                    "nombre": categoria.nombre,
                    "id_tipo_categoria": categoria.id_tipo_categoria,
                    "tipo_nombre": categoria.tipo_categoria.nombre
                    if categoria.tipo_categoria
                    else None,
                    "productos_count": productos_count,
                }
            )

        return jsonify(result), 200
    finally:
        db.close()


@categorias_bp.route("/", methods=["POST"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente")
def crear_categoria(user_id, user_rol, id_local):
    """Crear una nueva categoria"""
    try:
        data = CategoriaCreateSchema(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": "Datos invalidos", "details": e.errors()}), 400

    db = get_session()
    try:
        # Verificar que el tipo de categoria existe
        tipo = db.execute(
            select(TipoCategoria).where(TipoCategoria.id == data.id_tipo_categoria)
        ).scalar_one_or_none()

        if not tipo:
            return jsonify({"error": "Tipo de categoria no valido"}), 400

        # Buscar si existe una categoria con el mismo nombre (activa o eliminada)
        existente = db.execute(
            select(Categoria).where(
                func.lower(Categoria.nombre) == func.lower(data.nombre),
                Categoria.id_local == id_local,
            )
        ).scalar_one_or_none()

        if existente:
            if existente.eliminado_el is None:
                # Ya existe y esta activa
                return jsonify(
                    {"error": "Ya existe una categoria con ese nombre en este local"}
                ), 400
            else:
                # Existe pero fue eliminada - reactivarla
                existente.eliminado_el = None
                existente.id_tipo_categoria = data.id_tipo_categoria
                db.commit()
                db.refresh(existente)

                return jsonify(
                    {
                        "message": "Categoria reactivada exitosamente",
                        "categoria": {
                            "id": existente.id,
                            "nombre": existente.nombre,
                            "id_tipo_categoria": existente.id_tipo_categoria,
                            "tipo_nombre": tipo.nombre,
                        },
                    }
                ), 201

        # No existe, crear nueva
        nueva_categoria = Categoria(
            id_local=id_local,
            nombre=data.nombre,
            id_tipo_categoria=data.id_tipo_categoria,
        )
        db.add(nueva_categoria)
        db.commit()
        db.refresh(nueva_categoria)

        return jsonify(
            {
                "message": "Categoria creada exitosamente",
                "categoria": {
                    "id": nueva_categoria.id,
                    "nombre": nueva_categoria.nombre,
                    "id_tipo_categoria": nueva_categoria.id_tipo_categoria,
                    "tipo_nombre": tipo.nombre,
                },
            }
        ), 201
    finally:
        db.close()


@categorias_bp.route("/<int:categoria_id>", methods=["PUT"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente")
def actualizar_categoria(categoria_id, user_id, user_rol, id_local):
    """Actualizar una categoria"""
    try:
        data = CategoriaUpdateSchema(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": "Datos invalidos", "details": e.errors()}), 400

    db = get_session()
    try:
        categoria = db.execute(
            select(Categoria).where(
                Categoria.id == categoria_id,
                Categoria.id_local == id_local,
                Categoria.eliminado_el.is_(None),
            )
        ).scalar_one_or_none()

        if not categoria:
            return jsonify({"error": "Categoria no encontrada"}), 404

        if data.nombre is not None:
            existente = db.execute(
                select(Categoria).where(
                    func.lower(Categoria.nombre) == func.lower(data.nombre),
                    Categoria.id_local == id_local,
                    Categoria.id != categoria_id,
                    Categoria.eliminado_el.is_(None),
                )
            ).scalar_one_or_none()

            if existente:
                return jsonify(
                    {"error": "Ya existe una categoria con ese nombre en este local"}
                ), 400

            categoria.nombre = data.nombre

        if data.id_tipo_categoria is not None:
            # Verificar que el tipo existe
            tipo = db.execute(
                select(TipoCategoria).where(TipoCategoria.id == data.id_tipo_categoria)
            ).scalar_one_or_none()

            if not tipo:
                return jsonify({"error": "Tipo de categoria no valido"}), 400

            categoria.id_tipo_categoria = data.id_tipo_categoria

        db.commit()
        db.refresh(categoria)

        return jsonify(
            {
                "message": "Categoria actualizada",
                "categoria": {
                    "id": categoria.id,
                    "nombre": categoria.nombre,
                    "id_tipo_categoria": categoria.id_tipo_categoria,
                    "tipo_nombre": categoria.tipo_categoria.nombre
                    if categoria.tipo_categoria
                    else None,
                },
            }
        ), 200
    finally:
        db.close()


@categorias_bp.route("/<int:categoria_id>", methods=["DELETE"])
@requerir_auth
@requerir_empleado
@requerir_roles_empresa("gerente")
def eliminar_categoria(categoria_id, user_id, user_rol, id_local):
    """Eliminar una categoria"""
    db = get_session()
    try:
        categoria = db.execute(
            select(Categoria).where(
                Categoria.id == categoria_id,
                Categoria.id_local == id_local,
                Categoria.eliminado_el.is_(None),
            )
        ).scalar_one_or_none()

        if not categoria:
            return jsonify({"error": "Categoria no encontrada"}), 404

        # Soft delete - marcar como eliminada
        # Los productos que usan esta categoria mantendran su referencia
        categoria.eliminado_el = func.now()
        db.commit()

        return jsonify({"message": "Categoria eliminada exitosamente"}), 200
    finally:
        db.close()
