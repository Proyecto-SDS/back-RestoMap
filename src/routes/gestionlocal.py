"""
Rutas para Gestión de Locales
Endpoints para administrar mesas y productos de un local específico
"""
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import joinedload
from datetime import datetime
import logging
import bcrypt
from database import db_session
from models import Mesa, Producto, Local, Categoria, Usuario, Rol, EstadoMesaEnum, EstadoProductoEnum, Reserva, ReservaMesa, EstadoReservaEnum
from utils.jwt_helper import requerir_auth

logger = logging.getLogger(__name__)

gestionlocal_bp = Blueprint('gestionlocal', __name__, url_prefix='/api/gestionlocal')

# ============================================
# ENDPOINTS DE ESTADÍSTICAS DEL DASHBOARD
# ============================================

@gestionlocal_bp.route('/dashboard/stats', methods=['GET'])
@requerir_auth
def obtener_estadisticas_dashboard(user_id, user_rol):
    """
    Obtiene estadísticas del dashboard para el local del usuario
    GET /api/gestionlocal/dashboard/stats
    """
    try:
        # Obtener el local del usuario
        usuario = db_session.query(Usuario).filter_by(id=user_id).first()
        
        if not usuario or not usuario.id_local:
            return jsonify({"error": "Usuario sin local asignado"}), 403
        
        id_local = usuario.id_local
        
        # Contar productos del local
        total_productos = db_session.query(Producto).filter_by(id_local=id_local).count()
        productos_disponibles = db_session.query(Producto).filter_by(
            id_local=id_local,
            estado=EstadoProductoEnum.DISPONIBLE
        ).count()
        productos_agotados = db_session.query(Producto).filter_by(
            id_local=id_local,
            estado=EstadoProductoEnum.AGOTADO
        ).count()
        
        # Contar mesas del local
        from datetime import datetime, timedelta
        
        total_mesas = db_session.query(Mesa).filter_by(id_local=id_local).count()
        
        # Mesas físicamente ocupadas
        mesas_ocupadas = db_session.query(Mesa).filter_by(
            id_local=id_local,
            estado=EstadoMesaEnum.OCUPADA
        ).count()
        
        # Calcular mesas reservadas dinámicamente (solo las que tienen reserva activa AHORA)
        ahora = datetime.now()
        fecha_hoy = ahora.date()
        hora_inicio = (ahora - timedelta(minutes=30)).time()
        hora_fin = (ahora + timedelta(hours=2)).time()
        
        mesas_reservadas = db_session.query(Mesa.id)\
            .join(ReservaMesa)\
            .join(Reserva)\
            .filter(
                Mesa.id_local == id_local,
                Reserva.fecha_reserva == fecha_hoy,
                Reserva.hora_reserva >= hora_inicio,
                Reserva.hora_reserva <= hora_fin,
                Reserva.estado.in_([EstadoReservaEnum.PENDIENTE, EstadoReservaEnum.CONFIRMADA]),
                Mesa.estado != EstadoMesaEnum.OCUPADA,  # No contar las ya ocupadas
                Mesa.estado != EstadoMesaEnum.FUERA_DE_SERVICIO
            )\
            .distinct()\
            .count()
        
        # Mesas disponibles = total - ocupadas - reservadas activamente
        mesas_disponibles = total_mesas - mesas_ocupadas - mesas_reservadas
        
        # Contar reservas del local
        total_reservas = db_session.query(Reserva).filter_by(id_local=id_local).count()
        reservas_pendientes = db_session.query(Reserva).filter_by(
            id_local=id_local,
            estado=EstadoReservaEnum.PENDIENTE
        ).count()
        reservas_confirmadas = db_session.query(Reserva).filter_by(
            id_local=id_local,
            estado=EstadoReservaEnum.CONFIRMADA
        ).count()
        
        return jsonify({
            "productos": {
                "total": total_productos,
                "disponibles": productos_disponibles,
                "agotados": productos_agotados
            },
            "mesas": {
                "total": total_mesas,
                "disponibles": mesas_disponibles,
                "ocupadas": mesas_ocupadas,
                "reservadas": mesas_reservadas
            },
            "reservas": {
                "total": total_reservas,
                "pendientes": reservas_pendientes,
                "confirmadas": reservas_confirmadas
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error al obtener estadísticas del dashboard: {e}")
        return jsonify({"error": "Error al obtener las estadísticas"}), 500

# ============================================
# ENDPOINTS DE PERSONAL
# ============================================

@gestionlocal_bp.route('/personal', methods=['GET'])
@requerir_auth
def obtener_personal(user_id, user_rol):
    """
    Obtiene el personal del local (bartenders, meseros y chefs - excluye gerentes y clientes)
    GET /api/gestionlocal/personal
    """
    try:
        # Obtener el local del usuario
        usuario = db_session.query(Usuario).filter_by(id=user_id).first()
        
        if not usuario or not usuario.id_local:
            return jsonify({"error": "Usuario sin local asignado"}), 403
        
        id_local = usuario.id_local
        
        # Obtener solo bartenders, meseros y chefs del local
        # Excluimos gerentes y clientes
        personal = db_session.query(Usuario).join(Rol).filter(
            Usuario.id_local == id_local,
            Rol.nombre.in_(['bartender', 'mesero', 'chef'])
        ).all()
        
        resultado = []
        for empleado in personal:
            resultado.append({
                "id": empleado.id,
                "nombre": empleado.nombre,
                "correo": empleado.correo,
                "telefono": empleado.telefono,
                "rol": empleado.rol.nombre if empleado.rol else "Sin rol",
                "fecha_registro": empleado.creado_el.isoformat() if empleado.creado_el else None
            })
        
        return jsonify({
            "personal": resultado,
            "total": len(resultado)
        }), 200
        
    except Exception as e:
        logger.error(f"Error al obtener el personal: {e}")
        return jsonify({"error": "Error al obtener el personal"}), 500


@gestionlocal_bp.route('/personal', methods=['POST'])
@requerir_auth
def crear_empleado(user_id, user_rol):
    """
    Crea un nuevo empleado vinculado al local del gerente
    Solo accesible para usuarios con rol de gerente
    POST /api/gestionlocal/personal
    
    Body:
        {
            "nombre": "Carlos Mesero",
            "correo": "carlos@restaurante.cl",
            "telefono": "+56912345678",
            "contrasena": "password123",
            "rol": "mesero"  // "chef", "mesero", "bartender"
        }
        
    Response 201:
        {
            "success": true,
            "message": "Empleado creado exitosamente",
            "empleado": {
                "id": 10,
                "nombre": "Carlos Mesero",
                "correo": "carlos@restaurante.cl",
                "telefono": "+56912345678",
                "rol": "mesero",
                "id_local": 1
            }
        }
        
    Response 403:
        {"error": "Solo gerentes pueden crear empleados"}
    """
    try:
        # Verificar que el usuario tiene un local asignado Y es gerente
        usuario = db_session.query(Usuario).options(joinedload(Usuario.rol)).filter_by(id=user_id).first()
        
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404
            
        if not usuario.id_local:
            return jsonify({"error": "Usuario sin local asignado"}), 403
        
        # Validar que el usuario sea gerente (id_rol = 2 o rol.nombre = 'gerente')
        if not usuario.rol or usuario.rol.nombre != 'gerente':
            return jsonify({"error": "Solo gerentes pueden crear empleados"}), 403
        
        id_local = usuario.id_local
        
        # Obtener datos del request
        data = request.get_json()
        
        nombre = data.get('nombre')
        correo = data.get('correo')
        telefono = data.get('telefono')
        contrasena = data.get('contrasena')
        rol_nombre = data.get('rol', '').lower()
        
        # Validar campos requeridos
        if not nombre or not correo or not contrasena or not rol_nombre:
            return jsonify({"error": "Nombre, correo, contraseña y rol son requeridos"}), 400
        
        # Validar que el rol sea válido (solo operativos)
        roles_permitidos = ['chef', 'mesero', 'bartender']
        if rol_nombre not in roles_permitidos:
            return jsonify({
                "error": f"Rol inválido. Debe ser uno de: {', '.join(roles_permitidos)}"
            }), 400
        
        # Verificar que el correo no esté registrado
        usuario_existente = db_session.query(Usuario).filter_by(correo=correo).first()
        if usuario_existente:
            return jsonify({"error": "El correo ya está registrado"}), 400
        
        # Obtener el ID del rol
        rol_map = {
            'chef': 3,
            'mesero': 4,
            'bartender': 5
        }
        id_rol = rol_map.get(rol_nombre)
        
        # Encriptar contraseña
        contrasena_hash = bcrypt.hashpw(contrasena.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Crear nuevo empleado
        nuevo_empleado = Usuario(
            nombre=nombre,
            correo=correo,
            telefono=telefono,
            contrasena=contrasena_hash,
            id_rol=id_rol,
            id_local=id_local,  # Vincular al local del gerente
            creado_el=datetime.utcnow()
        )
        
        db_session.add(nuevo_empleado)
        db_session.commit()
        
        return jsonify({
            "success": True,
            "message": "Empleado creado exitosamente",
            "empleado": {
                "id": nuevo_empleado.id,
                "nombre": nuevo_empleado.nombre,
                "correo": nuevo_empleado.correo,
                "telefono": nuevo_empleado.telefono,
                "rol": rol_nombre,
                "id_local": id_local,
                "fecha_registro": nuevo_empleado.creado_el.isoformat() if nuevo_empleado.creado_el else None
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error al crear empleado: {e}")
        db_session.rollback()
        return jsonify({"error": "Error al crear el empleado", "detalle": str(e)}), 500

# ============================================
# ENDPOINTS DE CATEGORÍAS
# ============================================

@gestionlocal_bp.route('/categorias', methods=['GET'])
def obtener_categorias():
    """
    Obtiene todas las categorías disponibles
    GET /api/gestionlocal/categorias
    """
    try:
        categorias = db_session.query(Categoria).all()
        
        resultado = []
        for cat in categorias:
            resultado.append({
                "id": cat.id,
                "nombre": cat.nombre
            })
        
        return jsonify({
            "categorias": resultado,
            "total": len(resultado)
        }), 200
        
    except Exception as e:
        logger.error(f"Error al obtener categorías: {e}")
        return jsonify({"error": "Error al obtener las categorías"}), 500



# ============================================
# MANEJO DE ERRORES
# ============================================

@gestionlocal_bp.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Recurso no encontrado"}), 404


# ============================================
# ENDPOINTS PARA GERENTES (usa id_local del usuario)
# ============================================

@gestionlocal_bp.route('/mis-mesas', methods=['GET'])
@requerir_auth
def obtener_mis_mesas(user_id, user_rol):
    """
    Obtiene todas las mesas del local vinculado al usuario autenticado
    GET /api/gestionlocal/mis-mesas
    
    Requiere que el usuario tenga id_local configurado
    El estado de cada mesa se calcula dinámicamente basándose en:
    - Estado base de la mesa (ocupada, fuera_de_servicio)
    - Reservas activas que coincidan con la hora actual (±30 min)
    """
    try:
        from datetime import datetime, timedelta, time
        
        # Obtener el usuario para verificar su id_local
        usuario = db_session.query(Usuario).filter(Usuario.id == user_id).first()
        
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404
            
        if not usuario.id_local:
            return jsonify({"error": "Usuario no vinculado a ningún local"}), 404
        
        id_local = usuario.id_local
        
        # Obtener el local
        local = db_session.query(Local).filter_by(id=id_local).first()
        if not local:
            return jsonify({"error": "Local no encontrado"}), 404
        
        # Obtener mesas del local
        mesas = db_session.query(Mesa).filter_by(id_local=id_local).all()
        
        # Fecha y hora actual
        ahora = datetime.now()
        fecha_hoy = ahora.date()
        hora_actual = ahora.time()
        
        # Rango de tolerancia: 30 minutos antes y 2 horas después
        hora_inicio = (ahora - timedelta(minutes=30)).time()
        hora_fin = (ahora + timedelta(hours=2)).time()
        
        # Obtener todas las reservas activas de hoy para este local
        reservas_activas = db_session.query(ReservaMesa.id_mesa)\
            .join(Reserva)\
            .filter(
                Reserva.id_local == id_local,
                Reserva.fecha_reserva == fecha_hoy,
                Reserva.hora_reserva >= hora_inicio,
                Reserva.hora_reserva <= hora_fin,
                Reserva.estado.in_([EstadoReservaEnum.PENDIENTE, EstadoReservaEnum.CONFIRMADA])
            )\
            .all()
        
        # Crear set de IDs de mesas con reservas activas
        mesas_reservadas_ids = {r.id_mesa for r in reservas_activas}
        
        resultado = []
        for mesa in mesas:
            # Calcular estado dinámico
            if mesa.estado == EstadoMesaEnum.OCUPADA:
                # Si está ocupada físicamente, respeta ese estado
                estado_actual = "ocupada"
            elif mesa.estado == EstadoMesaEnum.FUERA_DE_SERVICIO:
                # Si está fuera de servicio, respeta ese estado
                estado_actual = "fuera_de_servicio"
            elif mesa.id in mesas_reservadas_ids:
                # Si tiene una reserva activa en este momento, mostrar como reservada
                estado_actual = "reservada"
            else:
                # De lo contrario, está disponible
                estado_actual = "disponible"
            
            resultado.append({
                "id": mesa.id,
                "nombre": mesa.nombre,
                "descripcion": mesa.descripcion,
                "capacidad": mesa.capacidad,
                "estado": estado_actual,
                "estado_base": mesa.estado.value if mesa.estado else None,  # Estado físico real
                "id_local": mesa.id_local
            })
        
        return jsonify({
            "local_id": id_local,
            "local_nombre": local.nombre,
            "total_mesas": len(resultado),
            "mesas": resultado
        }), 200
        
    except Exception as e:
        logger.error(f"Error al obtener mesas del usuario {user_id}: {e}")
        return jsonify({"error": "Error al obtener las mesas", "detalle": str(e)}), 500


@gestionlocal_bp.route('/mis-mesas', methods=['POST'])
@requerir_auth
def crear_mi_mesa(user_id, user_rol):
    """
    Crea una nueva mesa en el local vinculado al usuario autenticado
    POST /api/gestionlocal/mis-mesas
    
    Body:
        {
            "nombre": "Mesa 11",
            "capacidad": 6,
            "estado": "disponible"
        }
    """
    try:
        # Obtener el usuario para verificar su id_local
        usuario = db_session.query(Usuario).filter(Usuario.id == user_id).first()
        
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404
            
        if not usuario.id_local:
            return jsonify({"error": "Usuario no vinculado a ningún local"}), 404
        
        id_local = usuario.id_local
        
        data = request.get_json()
        
        # Validar campos requeridos
        if 'nombre' not in data or not data['nombre']:
            return jsonify({"error": "El nombre es requerido"}), 400
        
        if 'capacidad' not in data:
            return jsonify({"error": "La capacidad es requerida"}), 400
        
        capacidad = int(data['capacidad'])
        if capacidad < 1:
            return jsonify({"error": "La capacidad debe ser al menos 1"}), 400
        
        # Validar estado
        estado_str = data.get('estado', 'disponible').lower()
        estados_map = {
            'disponible': EstadoMesaEnum.DISPONIBLE,
            'ocupada': EstadoMesaEnum.OCUPADA,
            'reservada': EstadoMesaEnum.RESERVADA,
            'fuera_de_servicio': EstadoMesaEnum.FUERA_DE_SERVICIO
        }
        
        if estado_str not in estados_map:
            return jsonify({"error": f"Estado inválido. Debe ser uno de: {', '.join(estados_map.keys())}"}), 400
        
        # Crear la mesa
        nueva_mesa = Mesa(
            nombre=data['nombre'],
            capacidad=capacidad,
            estado=estados_map[estado_str],
            id_local=id_local
        )
        
        db_session.add(nueva_mesa)
        db_session.commit()
        db_session.refresh(nueva_mesa)
        
        return jsonify({
            "mensaje": "Mesa creada exitosamente",
            "mesa": {
                "id": nueva_mesa.id,
                "nombre": nueva_mesa.nombre,
                "capacidad": nueva_mesa.capacidad,
                "estado": nueva_mesa.estado.value if nueva_mesa.estado else None,
                "id_local": nueva_mesa.id_local
            }
        }), 201
        
    except ValueError as e:
        logger.error(f"Error de validación al crear mesa: {e}")
        db_session.rollback()
        return jsonify({"error": "Datos inválidos", "detalle": str(e)}), 400
    except Exception as e:
        logger.error(f"Error al crear mesa: {e}")
        db_session.rollback()
        return jsonify({"error": "Error al crear la mesa", "detalle": str(e)}), 500


@gestionlocal_bp.route('/mis-productos', methods=['GET'])
@requerir_auth
def obtener_mis_productos(user_id, user_rol):
    """
    Obtiene todos los productos del local vinculado al usuario autenticado
    GET /api/gestionlocal/mis-productos
    
    Requiere que el usuario tenga id_local configurado
    """
    try:
        # Obtener el usuario para verificar su id_local
        usuario = db_session.query(Usuario).filter(Usuario.id == user_id).first()
        
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404
            
        if not usuario.id_local:
            return jsonify({"error": "Usuario no vinculado a ningún local"}), 404
        
        id_local = usuario.id_local
        
        # Obtener el local
        local = db_session.query(Local).filter_by(id=id_local).first()
        if not local:
            return jsonify({"error": "Local no encontrado"}), 404
        
        # Obtener productos del local con categoría
        productos = db_session.query(Producto)\
            .options(joinedload(Producto.categoria))\
            .filter_by(id_local=id_local)\
            .all()
        
        resultado = []
        for prod in productos:
            resultado.append({
                "id": prod.id,
                "nombre": prod.nombre,
                "descripcion": prod.descripcion,
                "precio": float(prod.precio) if prod.precio else 0.0,
                "estado": prod.estado.value if prod.estado else None,
                "id_local": prod.id_local,
                "id_categoria": prod.id_categoria,
                "categoria_nombre": prod.categoria.nombre if prod.categoria else None
            })
        
        return jsonify({
            "local_id": id_local,
            "local_nombre": local.nombre,
            "total_productos": len(resultado),
            "productos": resultado
        }), 200
        
    except Exception as e:
        logger.error(f"Error al obtener productos del usuario {user_id}: {e}")
        return jsonify({"error": "Error al obtener los productos", "detalle": str(e)}), 500


@gestionlocal_bp.route('/mis-productos', methods=['POST'])
@requerir_auth
def crear_mi_producto(user_id, user_rol):
    """
    Crea un nuevo producto en el local vinculado al usuario autenticado
    POST /api/gestionlocal/mis-productos
    
    Body:
        {
            "nombre": "Pizza Napolitana",
            "descripcion": "Pizza con tomate, mozzarella y albahaca",
            "precio": 8500,
            "estado": "disponible",
            "id_categoria": 2
        }
    """
    try:
        # Obtener el usuario para verificar su id_local
        usuario = db_session.query(Usuario).filter(Usuario.id == user_id).first()
        
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404
            
        if not usuario.id_local:
            return jsonify({"error": "Usuario no vinculado a ningún local"}), 404
        
        id_local = usuario.id_local
        
        data = request.get_json()
        
        # Validar campos requeridos
        if 'nombre' not in data or not data['nombre']:
            return jsonify({"error": "El nombre es requerido"}), 400
        
        if 'precio' not in data:
            return jsonify({"error": "El precio es requerido"}), 400
        
        precio = float(data['precio'])
        if precio < 0:
            return jsonify({"error": "El precio debe ser mayor o igual a 0"}), 400
        
        # Validar categoría si se proporciona
        id_categoria = data.get('id_categoria')
        if id_categoria:
            categoria = db_session.query(Categoria).filter_by(id=id_categoria).first()
            if not categoria:
                return jsonify({"error": "Categoría no encontrada"}), 404
        
        # Validar estado
        estado_str = data.get('estado', 'disponible').lower()
        estados_map = {
            'disponible': EstadoProductoEnum.DISPONIBLE,
            'agotado': EstadoProductoEnum.AGOTADO,
            'inactivo': EstadoProductoEnum.INACTIVO
        }
        
        if estado_str not in estados_map:
            return jsonify({"error": f"Estado inválido. Debe ser uno de: {', '.join(estados_map.keys())}"}), 400
        
        # Crear el producto
        nuevo_producto = Producto(
            nombre=data['nombre'],
            descripcion=data.get('descripcion', ''),
            precio=precio,
            estado=estados_map[estado_str],
            id_local=id_local,
            id_categoria=id_categoria
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
                "estado": nuevo_producto.estado.value if nuevo_producto.estado else None,
                "id_local": nuevo_producto.id_local,
                "id_categoria": nuevo_producto.id_categoria,
                "categoria_nombre": nuevo_producto.categoria.nombre if nuevo_producto.categoria else None
            }
        }), 201
        
    except ValueError as e:
        logger.error(f"Error de validación al crear producto: {e}")
        db_session.rollback()
        return jsonify({"error": "Datos inválidos", "detalle": str(e)}), 400
    except Exception as e:
        logger.error(f"Error al crear producto: {e}")
        db_session.rollback()
        return jsonify({"error": "Error al crear el producto", "detalle": str(e)}), 500


@gestionlocal_bp.route('/mis-productos/<int:id_producto>', methods=['PUT'])
@requerir_auth
def actualizar_mi_producto(user_id, user_rol, id_producto):
    """
    Actualiza un producto del local vinculado al usuario autenticado
    PUT /api/gestionlocal/mis-productos/<id_producto>
    
    Body:
        {
            "nombre": "Lomo a lo Pobre Premium",
            "descripcion": "Descripción actualizada",
            "precio": 15000,
            "estado": "disponible" | "agotado" | "inactivo",
            "id_categoria": 2
        }
    """
    try:
        # Obtener el usuario para verificar su id_local
        usuario = db_session.query(Usuario).filter(Usuario.id == user_id).first()
        
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404
            
        if not usuario.id_local:
            return jsonify({"error": "Usuario no vinculado a ningún local"}), 404
        
        id_local = usuario.id_local
        
        # Verificar que el producto existe y pertenece al local del usuario
        producto = db_session.query(Producto).filter_by(id=id_producto, id_local=id_local).first()
        if not producto:
            return jsonify({"error": "Producto no encontrado en tu local"}), 404
        
        data = request.get_json()
        
        # Actualizar campos si se proporcionan
        if 'nombre' in data:
            if not data['nombre']:
                return jsonify({"error": "El nombre no puede estar vacío"}), 400
            producto.nombre = data['nombre']
        
        if 'descripcion' in data:
            producto.descripcion = data['descripcion']
        
        if 'precio' in data:
            precio = float(data['precio'])
            if precio < 0:
                return jsonify({"error": "El precio debe ser mayor o igual a 0"}), 400
            producto.precio = precio
        
        if 'id_categoria' in data:
            if data['id_categoria'] is not None:
                categoria = db_session.query(Categoria).filter_by(id=data['id_categoria']).first()
                if not categoria:
                    return jsonify({"error": "Categoría no encontrada"}), 404
            producto.id_categoria = data['id_categoria']
        
        if 'estado' in data:
            estado_str = data['estado'].lower()
            
            # Mapeo de strings a valores del enum
            estados_map = {
                'disponible': EstadoProductoEnum.DISPONIBLE,
                'agotado': EstadoProductoEnum.AGOTADO,
                'inactivo': EstadoProductoEnum.INACTIVO
            }
            
            if estado_str not in estados_map:
                return jsonify({"error": f"Estado inválido. Debe ser uno de: {', '.join(estados_map.keys())}"}), 400
            
            producto.estado = estados_map[estado_str]
        
        db_session.commit()
        db_session.refresh(producto)
        
        return jsonify({
            "mensaje": "Producto actualizado exitosamente",
            "producto": {
                "id": producto.id,
                "nombre": producto.nombre,
                "descripcion": producto.descripcion,
                "precio": producto.precio,
                "estado": producto.estado.value if producto.estado else None,
                "id_local": producto.id_local,
                "id_categoria": producto.id_categoria,
                "categoria_nombre": producto.categoria.nombre if producto.categoria else None
            }
        }), 200
        
    except ValueError as e:
        logger.error(f"Error de validación al actualizar producto {id_producto}: {e}")
        db_session.rollback()
        return jsonify({"error": "Datos inválidos", "detalle": str(e)}), 400
    except Exception as e:
        logger.error(f"Error al actualizar producto {id_producto}: {e}")
        db_session.rollback()
        return jsonify({"error": "Error al actualizar el producto", "detalle": str(e)}), 500


@gestionlocal_bp.route('/mis-productos/<int:id_producto>', methods=['DELETE'])
@requerir_auth
def eliminar_mi_producto(user_id, user_rol, id_producto):
    """
    Elimina un producto del local vinculado al usuario autenticado
    DELETE /api/gestionlocal/mis-productos/<id_producto>
    """
    try:
        # Obtener el usuario para verificar su id_local
        usuario = db_session.query(Usuario).filter(Usuario.id == user_id).first()
        
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404
            
        if not usuario.id_local:
            return jsonify({"error": "Usuario no vinculado a ningún local"}), 404
        
        id_local = usuario.id_local
        
        # Verificar que el producto existe y pertenece al local del usuario
        producto = db_session.query(Producto).filter_by(id=id_producto, id_local=id_local).first()
        if not producto:
            return jsonify({"error": "Producto no encontrado en tu local"}), 404
        
        # Guardar información antes de eliminar
        producto_info = {
            "id": producto.id,
            "nombre": producto.nombre
        }
        
        db_session.delete(producto)
        db_session.commit()
        
        return jsonify({
            "mensaje": "Producto eliminado exitosamente",
            "producto": producto_info
        }), 200
        
    except Exception as e:
        logger.error(f"Error al eliminar producto {id_producto}: {e}")
        db_session.rollback()
        return jsonify({"error": "Error al eliminar el producto", "detalle": str(e)}), 500


@gestionlocal_bp.route('/mis-mesas/<int:id_mesa>', methods=['PUT'])
@requerir_auth
def actualizar_mi_mesa(user_id, user_rol, id_mesa):
    """
    Actualiza una mesa del local vinculado al usuario autenticado
    PUT /api/gestionlocal/mis-mesas/<id_mesa>
    
    Body:
        {
            "nombre": "Mesa 1",
            "capacidad": 4,
            "estado": "disponible" | "ocupada" | "reservada" | "fuera_de_servicio"
        }
    """
    try:
        # Obtener el usuario para verificar su id_local
        usuario = db_session.query(Usuario).filter(Usuario.id == user_id).first()
        
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404
            
        if not usuario.id_local:
            return jsonify({"error": "Usuario no vinculado a ningún local"}), 404
        
        id_local = usuario.id_local
        
        # Verificar que la mesa existe y pertenece al local del usuario
        mesa = db_session.query(Mesa).filter_by(id=id_mesa, id_local=id_local).first()
        if not mesa:
            return jsonify({"error": "Mesa no encontrada en tu local"}), 404
        
        data = request.get_json()
        
        # Actualizar campos si se proporcionan
        if 'nombre' in data:
            mesa.nombre = data['nombre']
        
        if 'capacidad' in data:
            capacidad = int(data['capacidad'])
            if capacidad < 1:
                return jsonify({"error": "La capacidad debe ser al menos 1"}), 400
            mesa.capacidad = capacidad
        
        if 'estado' in data:
            estado_str = data['estado'].lower()
            
            # Mapeo de strings a valores del enum
            estados_map = {
                'disponible': EstadoMesaEnum.DISPONIBLE,
                'ocupada': EstadoMesaEnum.OCUPADA,
                'reservada': EstadoMesaEnum.RESERVADA,
                'fuera_de_servicio': EstadoMesaEnum.FUERA_DE_SERVICIO
            }
            
            if estado_str not in estados_map:
                return jsonify({"error": f"Estado inválido. Debe ser uno de: {', '.join(estados_map.keys())}"}), 400
            
            mesa.estado = estados_map[estado_str]
        
        db_session.commit()
        
        return jsonify({
            "mensaje": "Mesa actualizada exitosamente",
            "mesa": {
                "id": mesa.id,
                "nombre": mesa.nombre,
                "capacidad": mesa.capacidad,
                "estado": mesa.estado.value if mesa.estado else None,
                "id_local": mesa.id_local
            }
        }), 200
        
    except ValueError as e:
        logger.error(f"Error de validación al actualizar mesa {id_mesa}: {e}")
        db_session.rollback()
        return jsonify({"error": "Datos inválidos", "detalle": str(e)}), 400
    except Exception as e:
        logger.error(f"Error al actualizar mesa {id_mesa}: {e}")
        db_session.rollback()
        return jsonify({"error": "Error al actualizar la mesa", "detalle": str(e)}), 500


@gestionlocal_bp.route('/mis-mesas/<int:id_mesa>', methods=['DELETE'])
@requerir_auth
def eliminar_mi_mesa(user_id, user_rol, id_mesa):
    """
    Elimina una mesa del local vinculado al usuario autenticado
    DELETE /api/gestionlocal/mis-mesas/<id_mesa>
    """
    try:
        # Obtener el usuario para verificar su id_local
        usuario = db_session.query(Usuario).filter(Usuario.id == user_id).first()
        
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404
            
        if not usuario.id_local:
            return jsonify({"error": "Usuario no vinculado a ningún local"}), 404
        
        id_local = usuario.id_local
        
        # Verificar que la mesa existe y pertenece al local del usuario
        mesa = db_session.query(Mesa).filter_by(id=id_mesa, id_local=id_local).first()
        if not mesa:
            return jsonify({"error": "Mesa no encontrada en tu local"}), 404
        
        # Verificar si la mesa tiene reservas activas
        reservas_activas = db_session.query(ReservaMesa).join(Reserva).filter(
            ReservaMesa.id_mesa == id_mesa,
            Reserva.estado.in_([EstadoReservaEnum.PENDIENTE, EstadoReservaEnum.CONFIRMADA])
        ).count()
        
        if reservas_activas > 0:
            return jsonify({
                "error": "No se puede eliminar la mesa porque tiene reservas activas",
                "reservas_activas": reservas_activas
            }), 400
        
        # Guardar información antes de eliminar
        mesa_info = {
            "id": mesa.id,
            "nombre": mesa.nombre
        }
        
        db_session.delete(mesa)
        db_session.commit()
        
        return jsonify({
            "mensaje": "Mesa eliminada exitosamente",
            "mesa": mesa_info
        }), 200
        
    except Exception as e:
        logger.error(f"Error al eliminar mesa {id_mesa}: {e}")
        db_session.rollback()
        return jsonify({"error": "Error al eliminar la mesa", "detalle": str(e)}), 500


@gestionlocal_bp.errorhandler(500)
def internal_error(error):
    db_session.rollback()
    return jsonify({"error": "Error interno del servidor"}), 500
