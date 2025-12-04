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
from models import Mesa, Producto, Local, Categoria, Usuario, Rol, EstadoMesaEnum, EstadoProductoEnum, Reserva, ReservaMesa, EstadoReservaEnum, LocalRol, LocalEmpleado, Permiso
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


# =============================
# Roles y Permisos a nivel Local
# =============================


@gestionlocal_bp.route('/personal/roles', methods=['POST'])
@requerir_auth
def crear_rol_local(user_id, user_rol):
    """Crear un rol específico para el local del gerente"""
    try:
        usuario = db_session.query(Usuario).filter_by(id=user_id).first()
        if not usuario or not usuario.id_local:
            return jsonify({'error': 'Usuario sin local asignado'}), 403
        if not usuario.rol or usuario.rol.nombre != 'gerente':
            return jsonify({'error': 'Solo gerentes pueden crear roles de local'}), 403
        data = request.get_json() or {}
        nombre = data.get('nombre', '').strip()
        descripcion = data.get('descripcion', '')
        if not nombre:
            return jsonify({'error': 'Nombre de rol requerido'}), 400
        # Verificar existencia
        existe = db_session.query(LocalRol).filter_by(id_local=usuario.id_local, nombre=nombre).first()
        if existe:
            return jsonify({'error': 'Ya existe un rol con ese nombre en el local'}), 400
        nuevo = LocalRol(id_local=usuario.id_local, nombre=nombre, descripcion=descripcion)
        db_session.add(nuevo)
        db_session.commit()
        return jsonify({'success': True, 'rol_id': nuevo.id}), 201
    except Exception as e:
        logger.error(f"Error al crear rol local: {e}")
        db_session.rollback()
        return jsonify({'error': 'Error al crear rol local'}), 500


@gestionlocal_bp.route('/personal/roles', methods=['GET'])
@requerir_auth
def listar_roles_local(user_id, user_rol):
    try:
        usuario = db_session.query(Usuario).filter_by(id=user_id).first()
        if not usuario or not usuario.id_local:
            return jsonify({'error': 'Usuario sin local asignado'}), 403
        roles = db_session.query(LocalRol).filter_by(id_local=usuario.id_local).all()
        return jsonify([{'id': r.id, 'nombre': r.nombre, 'descripcion': r.descripcion} for r in roles]), 200
    except Exception as e:
        logger.error(f"Error al listar roles locales: {e}")
        return jsonify({'error': 'Error al listar roles locales'}), 500


@gestionlocal_bp.route('/personal/roles/<int:rol_id>/permisos', methods=['PUT'])
@requerir_auth
def asignar_permisos_rol_local(user_id, user_rol, rol_id):
    try:
        usuario = db_session.query(Usuario).filter_by(id=user_id).first()
        if not usuario or not usuario.id_local:
            return jsonify({'error': 'Usuario sin local asignado'}), 403
        if not usuario.rol or usuario.rol.nombre != 'gerente':
            return jsonify({'error': 'Solo gerentes pueden asignar permisos a roles'}), 403
        data = request.get_json() or {}
        permisos_ids = data.get('permisos', [])
        rol = db_session.query(LocalRol).filter_by(id=rol_id, id_local=usuario.id_local).first()
        if not rol:
            return jsonify({'error': 'Rol no encontrado en tu local'}), 404
        # Asignar permisos (se usan Permiso globales)
        permisos_objs = []
        if permisos_ids:
            permisos_objs = db_session.query(Permiso).filter(Permiso.id.in_(permisos_ids)).all()
        rol.permisos = permisos_objs
        db_session.commit()
        return jsonify({'success': True}), 200
    except Exception as e:
        logger.error(f"Error al asignar permisos rol local: {e}")
        db_session.rollback()
        return jsonify({'error': 'Error al asignar permisos'}), 500


# =============================
# Invitaciones y gestión de personal operativo por Local (CU-11)
# =============================


@gestionlocal_bp.route('/personal/invite', methods=['POST'])
@requerir_auth
def invite_local_employee(user_id, user_rol):
    """Genera una invitación única para que un empleado se registre y se vincule al local"""
    try:
        usuario = db_session.query(Usuario).filter_by(id=user_id).first()
        if not usuario or not usuario.id_local:
            return jsonify({'error': 'Usuario sin local asignado'}), 403
        if not usuario.rol or usuario.rol.nombre != 'gerente':
            return jsonify({'error': 'Solo gerentes pueden invitar personal'}), 403
        data = request.get_json() or {}
        correo = data.get('correo', '').strip().lower()
        rol_nombre = data.get('rol', '')
        if not correo or not rol_nombre:
            return jsonify({'error': 'Correo y rol son requeridos'}), 400
        # Buscar rol local
        rol_local = db_session.query(LocalRol).filter_by(id_local=usuario.id_local, nombre=rol_nombre).first()
        if not rol_local:
            return jsonify({'error': 'Rol local no existe. Créalo primero.'}), 400
        # Generar código
        import uuid
        codigo = str(uuid.uuid4())
        # Verificar usuario existente
        usuario_existente = db_session.query(Usuario).filter_by(correo=correo).first()
        if usuario_existente:
            nuevo = LocalEmpleado(id_local=usuario.id_local, id_usuario=usuario_existente.id, id_local_rol=rol_local.id, invitacion_codigo=codigo, activo=False)
        else:
            nuevo = LocalEmpleado(id_local=usuario.id_local, id_usuario=None, id_local_rol=rol_local.id, invitacion_codigo=codigo, activo=False)
        db_session.add(nuevo)
        db_session.commit()
        # En producción enviar correo con el enlace que contiene el código
        return jsonify({'success': True, 'codigo_invitacion': codigo}), 201
    except Exception as e:
        logger.error(f"Error al generar invitación local: {e}")
        db_session.rollback()
        return jsonify({'error': 'Error al generar la invitación'}), 500


@gestionlocal_bp.route('/personal/invite/accept', methods=['POST'])
def accept_local_invite():
    """Aceptar invitación para unirse al local usando el código"""
    try:
        data = request.get_json() or {}
        codigo = data.get('codigo')
        if not codigo:
            return jsonify({'error': 'Código requerido'}), 400
        invit = db_session.query(LocalEmpleado).filter_by(invitacion_codigo=codigo).first()
        if not invit:
            return jsonify({'error': 'Código inválido'}), 404
        correo = data.get('correo', '').strip().lower()
        nombre = data.get('nombre', '').strip()
        contrasena = data.get('contrasena')
        telefono = data.get('telefono')
        # Si no existe usuario asociado, crear
        if not invit.id_usuario:
            if not correo or not nombre or not contrasena:
                return jsonify({'error': 'Se requieren nombre, correo y contraseña para crear la cuenta'}), 400
            usuario_existente = db_session.query(Usuario).filter_by(correo=correo).first()
            if usuario_existente:
                invit.id_usuario = usuario_existente.id
            else:
                import bcrypt
                hashed = bcrypt.hashpw(contrasena.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                # Asignar rol global por defecto 'cliente' o 'usuario' según seed; usaremos 'mesero' si rol global no found? Use 'cliente'
                rol_global = db_session.query(Rol).filter_by(nombre='cliente').first()
                rol_global_id = rol_global.id if rol_global else None
                nuevo_u = Usuario(nombre=nombre, correo=correo, contrasena=hashed, telefono=telefono, id_rol=rol_global_id, id_local=invit.id_local, creado_el=datetime.utcnow())
                db_session.add(nuevo_u)
                db_session.flush()
                invit.id_usuario = nuevo_u.id
        # Vincular el usuario al local y marcar aceptado
        usuario_obj = db_session.query(Usuario).filter_by(id=invit.id_usuario).first()
        if usuario_obj and not usuario_obj.id_local:
            usuario_obj.id_local = invit.id_local
        invit.aceptado_el = datetime.utcnow()
        invit.activo = True
        invit.invitacion_codigo = None
        db_session.commit()
        return jsonify({'success': True, 'message': 'Invitación aceptada'}), 200
    except Exception as e:
        logger.error(f"Error al aceptar invitación local: {e}")
        db_session.rollback()
        return jsonify({'error': 'Error al aceptar la invitación'}), 500


@gestionlocal_bp.route('/personal/invitaciones', methods=['GET'])
@requerir_auth
def listar_invitaciones_local(user_id, user_rol):
    try:
        usuario = db_session.query(Usuario).filter_by(id=user_id).first()
        if not usuario or not usuario.id_local:
            return jsonify({'error': 'Usuario sin local asignado'}), 403
        if not usuario.rol or usuario.rol.nombre != 'gerente':
            return jsonify({'error': 'Solo gerentes pueden listar invitaciones'}), 403
        invs = db_session.query(LocalEmpleado).filter_by(id_local=usuario.id_local, activo=False).all()
        return jsonify([{'id': i.id, 'correo': i.usuario.correo if i.usuario else None, 'rol': i.local_rol.nombre if i.local_rol else None, 'codigo': i.invitacion_codigo} for i in invs]), 200
    except Exception as e:
        logger.error(f"Error al listar invitaciones: {e}")
        return jsonify({'error': 'Error al listar invitaciones'}), 500


@gestionlocal_bp.route('/personal/<int:empleado_id>', methods=['PUT'])
@requerir_auth
def actualizar_empleado_local(user_id, user_rol, empleado_id):
    try:
        usuario = db_session.query(Usuario).filter_by(id=user_id).first()
        if not usuario or not usuario.id_local:
            return jsonify({'error': 'Usuario sin local asignado'}), 403
        if not usuario.rol or usuario.rol.nombre != 'gerente':
            return jsonify({'error': 'Solo gerentes pueden actualizar empleados'}), 403
        data = request.get_json() or {}
        activo = data.get('activo')
        rol_nombre = data.get('rol')
        le = db_session.query(LocalEmpleado).filter_by(id=empleado_id, id_local=usuario.id_local).first()
        if not le:
            return jsonify({'error': 'Empleado no encontrado en tu local'}), 404
        if activo is not None:
            le.activo = bool(activo)
        if rol_nombre:
            rol_local = db_session.query(LocalRol).filter_by(id_local=usuario.id_local, nombre=rol_nombre).first()
            if not rol_local:
                return jsonify({'error': 'Rol local no encontrado'}), 400
            le.id_local_rol = rol_local.id
        db_session.commit()
        return jsonify({'success': True}), 200
    except Exception as e:
        logger.error(f"Error al actualizar empleado local: {e}")
        db_session.rollback()
        return jsonify({'error': 'Error al actualizar empleado'}), 500

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
