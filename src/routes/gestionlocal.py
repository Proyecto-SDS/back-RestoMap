"""
Rutas para Gestión de Locales
Endpoints para administrar mesas y productos de un local específico
"""
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import joinedload
from database import db_session
from models import Mesa, Producto, Local, Categoria, EstadoMesaEnum, EstadoProductoEnum
import logging

logger = logging.getLogger(__name__)

gestionlocal_bp = Blueprint('gestionlocal', __name__, url_prefix='/api/gestionlocal')

# ============================================
# ENDPOINTS DE MESAS
# ============================================

@gestionlocal_bp.route('/locales/<int:id_local>/mesas', methods=['GET'])
def obtener_mesas_local(id_local):
    """
    Obtiene todas las mesas de un local específico
    GET /api/gestionlocal/locales/<id_local>/mesas
    """
    try:
        # Verificar que el local existe
        local = db_session.query(Local).filter_by(id=id_local).first()
        if not local:
            return jsonify({"error": "Local no encontrado"}), 404
        
        # Obtener mesas del local
        mesas = db_session.query(Mesa).filter_by(id_local=id_local).all()
        
        resultado = []
        for mesa in mesas:
            resultado.append({
                "id": mesa.id,
                "nombre": mesa.nombre,
                "descripcion": mesa.descripcion,
                "capacidad": mesa.capacidad,
                "estado": mesa.estado.value if mesa.estado else None,
                "id_local": mesa.id_local
            })
        
        return jsonify({
            "local_id": id_local,
            "local_nombre": local.nombre,
            "total_mesas": len(resultado),
            "mesas": resultado
        }), 200
        
    except Exception as e:
        logger.error(f"Error al obtener mesas del local {id_local}: {e}")
        db_session.rollback()
        return jsonify({"error": "Error al obtener las mesas", "detalle": str(e)}), 500


@gestionlocal_bp.route('/locales/<int:id_local>/mesas', methods=['POST'])
def crear_mesa_local(id_local):
    """
    Crea una nueva mesa para un local específico
    POST /api/gestionlocal/locales/<id_local>/mesas
    Body: {
        "nombre": "Mesa 1",
        "descripcion": "Mesa junto a la ventana",
        "capacidad": 4,
        "estado": "disponible"  // opcional, por defecto "disponible"
    }
    """
    try:
        # Verificar que el local existe
        local = db_session.query(Local).filter_by(id=id_local).first()
        if not local:
            return jsonify({"error": "Local no encontrado"}), 404
        
        data = request.get_json()
        
        # Validaciones
        if not data.get('nombre'):
            return jsonify({"error": "El nombre de la mesa es obligatorio"}), 400
        
        if not data.get('capacidad') or data.get('capacidad') <= 0:
            return jsonify({"error": "La capacidad debe ser un número mayor a 0"}), 400
        
        # Validar estado si se proporciona
        estado = data.get('estado', 'disponible')
        try:
            estado_enum = EstadoMesaEnum(estado)
        except ValueError:
            return jsonify({
                "error": f"Estado inválido. Valores permitidos: {[e.value for e in EstadoMesaEnum]}"
            }), 400
        
        # Crear nueva mesa
        nueva_mesa = Mesa(
            id_local=id_local,
            nombre=data['nombre'],
            descripcion=data.get('descripcion'),
            capacidad=data['capacidad'],
            estado=estado_enum
        )
        
        db_session.add(nueva_mesa)
        db_session.commit()
        db_session.refresh(nueva_mesa)
        
        return jsonify({
            "mensaje": "Mesa creada exitosamente",
            "mesa": {
                "id": nueva_mesa.id,
                "nombre": nueva_mesa.nombre,
                "descripcion": nueva_mesa.descripcion,
                "capacidad": nueva_mesa.capacidad,
                "estado": nueva_mesa.estado.value,
                "id_local": nueva_mesa.id_local
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error al crear mesa en local {id_local}: {e}")
        db_session.rollback()
        return jsonify({"error": "Error al crear la mesa", "detalle": str(e)}), 500


@gestionlocal_bp.route('/locales/<int:id_local>/mesas/<int:id_mesa>', methods=['PUT'])
def editar_mesa_local(id_local, id_mesa):
    """
    Edita una mesa de un local específico
    PUT /api/gestionlocal/locales/<id_local>/mesas/<id_mesa>
    Body: {
        "nombre": "Mesa VIP 1",  // opcional
        "descripcion": "Mesa premium junto a la ventana",  // opcional
        "capacidad": 6,  // opcional
        "estado": "ocupada"  // opcional
    }
    """
    try:
        # Verificar que la mesa existe y pertenece al local
        mesa = db_session.query(Mesa).filter_by(id=id_mesa, id_local=id_local).first()
        if not mesa:
            return jsonify({"error": "Mesa no encontrada en este local"}), 404
        
        data = request.get_json()
        
        # Actualizar campos proporcionados
        if 'nombre' in data:
            if not data['nombre']:
                return jsonify({"error": "El nombre no puede estar vacío"}), 400
            mesa.nombre = data['nombre']
        
        if 'descripcion' in data:
            mesa.descripcion = data['descripcion']
        
        if 'capacidad' in data:
            if data['capacidad'] <= 0:
                return jsonify({"error": "La capacidad debe ser mayor a 0"}), 400
            mesa.capacidad = data['capacidad']
        
        if 'estado' in data:
            try:
                estado_enum = EstadoMesaEnum(data['estado'])
                mesa.estado = estado_enum
            except ValueError:
                return jsonify({
                    "error": f"Estado inválido. Valores permitidos: {[e.value for e in EstadoMesaEnum]}"
                }), 400
        
        db_session.commit()
        db_session.refresh(mesa)
        
        return jsonify({
            "mensaje": "Mesa actualizada exitosamente",
            "mesa": {
                "id": mesa.id,
                "nombre": mesa.nombre,
                "descripcion": mesa.descripcion,
                "capacidad": mesa.capacidad,
                "estado": mesa.estado.value,
                "id_local": mesa.id_local
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error al editar mesa {id_mesa} del local {id_local}: {e}")
        db_session.rollback()
        return jsonify({"error": "Error al actualizar la mesa", "detalle": str(e)}), 500


@gestionlocal_bp.route('/locales/<int:id_local>/mesas/<int:id_mesa>', methods=['DELETE'])
def eliminar_mesa_local(id_local, id_mesa):
    """
    Elimina una mesa de un local específico
    DELETE /api/gestionlocal/locales/<id_local>/mesas/<id_mesa>
    """
    try:
        # Verificar que la mesa existe y pertenece al local
        mesa = db_session.query(Mesa).filter_by(id=id_mesa, id_local=id_local).first()
        if not mesa:
            return jsonify({"error": "Mesa no encontrada en este local"}), 404
        
        nombre_mesa = mesa.nombre
        
        db_session.delete(mesa)
        db_session.commit()
        
        return jsonify({
            "mensaje": f"Mesa '{nombre_mesa}' eliminada exitosamente",
            "id_mesa": id_mesa
        }), 200
        
    except Exception as e:
        logger.error(f"Error al eliminar mesa {id_mesa} del local {id_local}: {e}")
        db_session.rollback()
        return jsonify({"error": "Error al eliminar la mesa", "detalle": str(e)}), 500


# ============================================
# ENDPOINTS DE PRODUCTOS
# ============================================

@gestionlocal_bp.route('/locales/<int:id_local>/productos', methods=['GET'])
def obtener_productos_local(id_local):
    """
    Obtiene todos los productos de un local específico
    GET /api/gestionlocal/locales/<id_local>/productos
    """
    try:
        # Verificar que el local existe
        local = db_session.query(Local).filter_by(id=id_local).first()
        if not local:
            return jsonify({"error": "Local no encontrado"}), 404
        
        # Obtener productos del local con su categoría
        productos = db_session.query(Producto)\
            .options(joinedload(Producto.categoria))\
            .filter_by(id_local=id_local).all()
        
        resultado = []
        for producto in productos:
            resultado.append({
                "id": producto.id,
                "nombre": producto.nombre,
                "descripcion": producto.descripcion,
                "precio": producto.precio,
                "estado": producto.estado.value if producto.estado else None,
                "id_local": producto.id_local,
                "id_categoria": producto.id_categoria,
                "categoria": producto.categoria.nombre if producto.categoria else None
            })
        
        return jsonify({
            "local_id": id_local,
            "local_nombre": local.nombre,
            "total_productos": len(resultado),
            "productos": resultado
        }), 200
        
    except Exception as e:
        logger.error(f"Error al obtener productos del local {id_local}: {e}")
        db_session.rollback()
        return jsonify({"error": "Error al obtener los productos", "detalle": str(e)}), 500


@gestionlocal_bp.route('/locales/<int:id_local>/productos', methods=['POST'])
def crear_producto_local(id_local):
    """
    Crea un nuevo producto para un local específico
    POST /api/gestionlocal/locales/<id_local>/productos
    Body: {
        "nombre": "Hamburguesa Clásica",
        "descripcion": "Hamburguesa con carne, lechuga, tomate y queso",
        "precio": 8500,
        "id_categoria": 2,  // opcional
        "estado": "disponible"  // opcional, por defecto "disponible"
    }
    """
    try:
        # Verificar que el local existe
        local = db_session.query(Local).filter_by(id=id_local).first()
        if not local:
            return jsonify({"error": "Local no encontrado"}), 404
        
        data = request.get_json()
        
        # Validaciones
        if not data.get('nombre'):
            return jsonify({"error": "El nombre del producto es obligatorio"}), 400
        
        if not data.get('precio') or data.get('precio') < 0:
            return jsonify({"error": "El precio debe ser un número mayor o igual a 0"}), 400
        
        # Validar categoría si se proporciona
        if data.get('id_categoria'):
            categoria = db_session.query(Categoria).filter_by(id=data['id_categoria']).first()
            if not categoria:
                return jsonify({"error": "Categoría no encontrada"}), 404
        
        # Validar estado si se proporciona
        estado = data.get('estado', 'disponible')
        try:
            estado_enum = EstadoProductoEnum(estado)
        except ValueError:
            return jsonify({
                "error": f"Estado inválido. Valores permitidos: {[e.value for e in EstadoProductoEnum]}"
            }), 400
        
        # Crear nuevo producto
        nuevo_producto = Producto(
            id_local=id_local,
            nombre=data['nombre'],
            descripcion=data.get('descripcion'),
            precio=data['precio'],
            id_categoria=data.get('id_categoria'),
            estado=estado_enum
        )
        
        db_session.add(nuevo_producto)
        db_session.commit()
        db_session.refresh(nuevo_producto)
        
        return jsonify({
            "mensaje": "Producto creado exitosamente",
            "producto": {
                "id": nuevo_producto.id,
                "nombre": nuevo_producto.nombre,
                "descripcion": nuevo_producto.descripcion,
                "precio": nuevo_producto.precio,
                "estado": nuevo_producto.estado.value,
                "id_local": nuevo_producto.id_local,
                "id_categoria": nuevo_producto.id_categoria,
                "categoria": nuevo_producto.categoria.nombre if nuevo_producto.categoria else None
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error al crear producto en local {id_local}: {e}")
        db_session.rollback()
        return jsonify({"error": "Error al crear el producto", "detalle": str(e)}), 500


@gestionlocal_bp.route('/locales/<int:id_local>/productos/<int:id_producto>', methods=['PUT'])
def editar_producto_local(id_local, id_producto):
    """
    Edita un producto de un local específico
    PUT /api/gestionlocal/locales/<id_local>/productos/<id_producto>
    Body: {
        "nombre": "Hamburguesa Premium",  // opcional
        "descripcion": "Hamburguesa gourmet con carne angus",  // opcional
        "precio": 12500,  // opcional
        "estado": "agotado",  // opcional
        "id_categoria": 3  // opcional
    }
    """
    try:
        # Verificar que el producto existe y pertenece al local
        producto = db_session.query(Producto).filter_by(id=id_producto, id_local=id_local).first()
        if not producto:
            return jsonify({"error": "Producto no encontrado en este local"}), 404
        
        data = request.get_json()
        
        # Actualizar campos proporcionados
        if 'nombre' in data:
            if not data['nombre']:
                return jsonify({"error": "El nombre no puede estar vacío"}), 400
            producto.nombre = data['nombre']
        
        if 'descripcion' in data:
            producto.descripcion = data['descripcion']
        
        if 'precio' in data:
            if data['precio'] < 0:
                return jsonify({"error": "El precio debe ser mayor o igual a 0"}), 400
            producto.precio = data['precio']
        
        if 'id_categoria' in data:
            if data['id_categoria'] is not None:
                categoria = db_session.query(Categoria).filter_by(id=data['id_categoria']).first()
                if not categoria:
                    return jsonify({"error": "Categoría no encontrada"}), 404
            producto.id_categoria = data['id_categoria']
        
        if 'estado' in data:
            try:
                estado_enum = EstadoProductoEnum(data['estado'])
                producto.estado = estado_enum
            except ValueError:
                return jsonify({
                    "error": f"Estado inválido. Valores permitidos: {[e.value for e in EstadoProductoEnum]}"
                }), 400
        
        db_session.commit()
        db_session.refresh(producto)
        
        return jsonify({
            "mensaje": "Producto actualizado exitosamente",
            "producto": {
                "id": producto.id,
                "nombre": producto.nombre,
                "descripcion": producto.descripcion,
                "precio": producto.precio,
                "estado": producto.estado.value,
                "id_local": producto.id_local,
                "id_categoria": producto.id_categoria,
                "categoria": producto.categoria.nombre if producto.categoria else None
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error al editar producto {id_producto} del local {id_local}: {e}")
        db_session.rollback()
        return jsonify({"error": "Error al actualizar el producto", "detalle": str(e)}), 500


@gestionlocal_bp.route('/locales/<int:id_local>/productos/<int:id_producto>', methods=['DELETE'])
def eliminar_producto_local(id_local, id_producto):
    """
    Elimina un producto de un local específico
    DELETE /api/gestionlocal/locales/<id_local>/productos/<id_producto>
    """
    try:
        # Verificar que el producto existe y pertenece al local
        producto = db_session.query(Producto).filter_by(id=id_producto, id_local=id_local).first()
        if not producto:
            return jsonify({"error": "Producto no encontrado en este local"}), 404
        
        nombre_producto = producto.nombre
        
        db_session.delete(producto)
        db_session.commit()
        
        return jsonify({
            "mensaje": f"Producto '{nombre_producto}' eliminado exitosamente",
            "id_producto": id_producto
        }), 200
        
    except Exception as e:
        logger.error(f"Error al eliminar producto {id_producto} del local {id_local}: {e}")
        db_session.rollback()
        return jsonify({"error": "Error al eliminar el producto", "detalle": str(e)}), 500


# ============================================
# MANEJO DE ERRORES
# ============================================

@gestionlocal_bp.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Recurso no encontrado"}), 404


@gestionlocal_bp.errorhandler(500)
def internal_error(error):
    db_session.rollback()
    return jsonify({"error": "Error interno del servidor"}), 500
