"""
Rutas de reservas
Endpoints: /api/reservas/*
"""
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import joinedload
from datetime import datetime, date, time

from database import db_session
from models import Reserva, ReservaMesa, Local, Mesa, Usuario, QRDinamico, Foto, Direccion
from models.models import EstadoReservaEnum, EstadoReservaMesaEnum
from utils.jwt_helper import requerir_auth
from services.qr_service import crear_qr_reserva, generar_qr_imagen
import json

reservas_bp = Blueprint('reservas', __name__, url_prefix='/api/reservas')


@reservas_bp.route('/', methods=['POST'])
@requerir_auth
def crear_reserva(user_id, user_rol):
    """
    Crear nueva reserva para un local
    
    Headers:
        Authorization: Bearer {token}
        
    Body:
        {
            "localId": "1",
            "mesaId": "1",
            "fecha": "2024-11-25",
            "hora": "19:30",
            "numeroPersonas": 4
        }
        
    Response 201:
        {
            "success": true,
            "message": "Reserva creada exitosamente",
            "reserva": {
                "id": 1,
                "localId": "1",
                "localNombre": "El Gran Sabor",
                "mesaId": "1",
                "mesaNombre": "Mesa 1",
                "fecha": "2024-11-25",
                "hora": "19:30",
                "estado": "pendiente",
                "numeroPersonas": 4
            }
        }
        
    Response 400:
        {"error": "localId, mesaId, fecha y hora son requeridos"}
        {"error": "Formato de fecha inválido"}
        {"error": "La fecha debe ser futura"}
        {"error": "Mesa no disponible para esta fecha y hora"}
        
    Response 404:
        {"error": "Local no encontrado"}
        {"error": "Mesa no encontrada"}
    """
    try:
        data = request.get_json()
        
        local_id = data.get('localId')
        mesa_id = data.get('mesaId')
        fecha_str = data.get('fecha')
        hora_str = data.get('hora')
        numero_personas = data.get('numeroPersonas', 2)
        
        # Validar campos requeridos
        if not local_id or not mesa_id or not fecha_str or not hora_str:
            return jsonify({'error': 'localId, mesaId, fecha y hora son requeridos'}), 400
        
        # Convertir IDs
        try:
            local_id = int(local_id)
            mesa_id = int(mesa_id)
        except ValueError:
            return jsonify({'error': 'localId y mesaId deben ser números'}), 400
        
        # Parsear fecha
        try:
            fecha_reserva = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Formato de fecha inválido. Use: YYYY-MM-DD'}), 400
        
        # Parsear hora
        try:
            hora_reserva = datetime.strptime(hora_str, '%H:%M').time()
        except ValueError:
            return jsonify({'error': 'Formato de hora inválido. Use: HH:MM'}), 400
        
        # Validar que la fecha sea futura (o hoy)
        if fecha_reserva < date.today():
            return jsonify({'error': 'La fecha debe ser futura'}), 400
        
        # Verificar que el local existe
        local = db_session.query(Local).filter(Local.id == local_id).first()
        if not local:
            return jsonify({'error': 'Local no encontrado'}), 404
        
        # Verificar que la mesa existe y pertenece al local
        mesa = db_session.query(Mesa)\
            .filter(Mesa.id == mesa_id, Mesa.id_local == local_id)\
            .first()
        
        if not mesa:
            return jsonify({'error': 'Mesa no encontrada en este local'}), 404
        
        # Verificar capacidad de la mesa
        if numero_personas > mesa.capacidad:
            return jsonify({
                'error': f'La mesa seleccionada tiene capacidad para {mesa.capacidad} personas'
            }), 400
        
        # Verificar disponibilidad de la mesa para esa fecha y hora
        # Considerar un rango de ±2 horas
        from datetime import timedelta
        
        hora_inicio = (datetime.combine(date.today(), hora_reserva) - timedelta(hours=2)).time()
        hora_fin = (datetime.combine(date.today(), hora_reserva) + timedelta(hours=2)).time()
        
        reservas_existentes = db_session.query(Reserva)\
            .join(ReservaMesa)\
            .filter(
                ReservaMesa.id_mesa == mesa_id,
                Reserva.fecha_reserva == fecha_reserva,
                Reserva.hora_reserva >= hora_inicio,
                Reserva.hora_reserva <= hora_fin,
                Reserva.estado.in_(['pendiente', 'confirmada'])
            )\
            .first()
        
        if reservas_existentes:
            return jsonify({
                'error': 'Mesa no disponible para esta fecha y hora. Por favor elija otro horario.'
            }), 400
        
        # Crear nueva reserva
        nueva_reserva = Reserva(
            id_local=local_id,
            id_usuario=user_id,
            fecha_reserva=fecha_reserva,
            hora_reserva=hora_reserva,
            estado=EstadoReservaEnum.PENDIENTE,
            creado_el=datetime.utcnow()
        )
        
        db_session.add(nueva_reserva)
        db_session.flush()  # Para obtener el ID
        
        # Crear relación reserva-mesa
        reserva_mesa = ReservaMesa(
            id_reserva=nueva_reserva.id,
            id_mesa=mesa_id,
            prioridad=EstadoReservaMesaEnum.ALTA
        )
        
        db_session.add(reserva_mesa)
        db_session.commit()
        
        # Generar QR dinámico para la reserva
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"[DEBUG] Generando QR para reserva {nueva_reserva.id}, mesa {mesa_id}")
            codigo_qr, qr_base64 = crear_qr_reserva(
                id_reserva=nueva_reserva.id,
                id_mesa=mesa_id,
                minutos_tolerancia=10  # Expira 10 minutos después de la hora de reserva
            )
            logger.info(f"[DEBUG] QR generado exitosamente. Código: {codigo_qr}")
            logger.info(f"[DEBUG] QR base64 length: {len(qr_base64) if qr_base64 else 0}")
        except Exception as e:
            import traceback
            logger.error(f"[ERROR] Fallo al generar QR: {str(e)}")
            logger.error(traceback.format_exc())
            # Si falla la generación del QR, no fallar toda la reserva
            codigo_qr = None
            qr_base64 = None
        
        return jsonify({
            'success': True,
            'message': 'Reserva creada exitosamente',
            'reserva': {
                'id': nueva_reserva.id,
                'localId': str(local_id),
                'localNombre': local.nombre,
                'mesaId': str(mesa_id),
                'mesaNombre': mesa.nombre,
                'fecha': fecha_str,
                'hora': hora_str,
                'estado': 'pendiente',
                'numeroPersonas': numero_personas,
                'codigoQR': codigo_qr,
                'qrImage': qr_base64
            }
        }), 201
        
    except Exception as e:
        db_session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Error al crear la reserva'}), 500


@reservas_bp.route('/mis-reservas', methods=['GET'])
@requerir_auth
def obtener_mis_reservas(user_id, user_rol):
    """
    Obtener todas las reservas del usuario autenticado
    
    Headers:
        Authorization: Bearer {token}
        
    Response 200:
        {
            "reservas": [
                {
                    "id": 1,
                    "localId": "1",
                    "localNombre": "El Gran Sabor",
                    "fecha": "2024-11-25",
                    "hora": "19:30",
                    "estado": "pendiente",
                    "mesas": ["Mesa 1", "Mesa 2"]
                }
            ]
        }
    """
    try:
        reservas = db_session.query(Reserva)\
            .options(
                joinedload(Reserva.local).joinedload(Local.direccion),
                joinedload(Reserva.local).joinedload(Local.fotos),
                joinedload(Reserva.local).joinedload(Local.tipo_local),
                joinedload(Reserva.reservas_mesa).joinedload(ReservaMesa.mesa),
                joinedload(Reserva.qr_dinamicos)
            )\
            .filter(Reserva.id_usuario == user_id)\
            .order_by(Reserva.fecha_reserva.desc(), Reserva.hora_reserva.desc())\
            .all()
        
        reservas_lista = []
        for reserva in reservas:
            mesas_nombres = [rm.mesa.nombre for rm in reserva.reservas_mesa if rm.mesa]
            
            # Obtener código QR activo
            qr_codigo = None
            if reserva.qr_dinamicos:
                # Buscar el QR más reciente o activo
                qr = next((q for q in reserva.qr_dinamicos if q.activo), None)
                if qr:
                    qr_codigo = qr.codigo
            
            # Obtener imagen del local (banner o primera foto)
            local_imagen = None
            if reserva.local and reserva.local.fotos:
                # Intentar buscar banner
                banner = next((f for f in reserva.local.fotos if f.id_tipo_foto == 1), None) # Asumiendo 1 es banner
                if banner:
                    local_imagen = banner.ruta
                else:
                    local_imagen = reserva.local.fotos[0].ruta
            
            # Obtener dirección
            direccion_str = ""
            if reserva.local and reserva.local.direccion:
                d = reserva.local.direccion
                direccion_str = f"{d.calle} {d.numero}"
                
            # Generar imagen QR si hay código
            qr_base64 = None
            if qr_codigo:
                try:
                    qr_data = {
                        "tipo": "reserva",
                        "codigo": qr_codigo,
                        "reserva_id": reserva.id,
                        "mesa_id": reserva.reservas_mesa[0].id_mesa if reserva.reservas_mesa else None,
                        "local_id": reserva.id_local,
                        "fecha": reserva.fecha_reserva.isoformat() if reserva.fecha_reserva else None,
                        "hora": reserva.hora_reserva.strftime("%H:%M") if reserva.hora_reserva else None
                    }
                    qr_string = json.dumps(qr_data)
                    qr_base64 = generar_qr_imagen(qr_string)
                except Exception as e:
                    print(f"Error generando QR para reserva {reserva.id}: {e}")

            reservas_lista.append({
                'id': reserva.id,
                'localId': str(reserva.id_local),
                'localNombre': reserva.local.nombre if reserva.local else 'Local',
                'localTipo': reserva.local.tipo_local.nombre if reserva.local and reserva.local.tipo_local else 'Restaurante',
                'localImagen': local_imagen,
                'localDireccion': direccion_str,
                'fecha': reserva.fecha_reserva.strftime('%Y-%m-%d') if reserva.fecha_reserva else None,
                'hora': reserva.hora_reserva.strftime('%H:%M') if reserva.hora_reserva else None,
                'estado': reserva.estado.value if reserva.estado else 'pendiente',
                'mesas': mesas_nombres,
                'codigoQR': qr_codigo or f"RES-{reserva.id}",
                'qrImage': qr_base64
            })
        
        return jsonify({'reservas': reservas_lista}), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Error al obtener las reservas'}), 500


@reservas_bp.route('/local', methods=['GET'])
@requerir_auth
def obtener_reservas_local(user_id, user_rol):
    """
    Obtener todas las reservas del local vinculado al gerente
    
    Headers:
        Authorization: Bearer {token}
        
    Response 200:
        {
            "reservas": [
                {
                    "id": 1,
                    "clientName": "Juan Pérez",
                    "clientEmail": "juan@test.cl",
                    "date": "2024-11-25",
                    "time": "19:30",
                    "pax": 4,
                    "status": "pendiente",
                    "table": "Mesa 1",
                    "requestDate": "Hace 2 horas"
                }
            ]
        }
        
    Response 403:
        {"error": "No tienes acceso a este recurso"}
        
    Response 404:
        {"error": "Usuario no vinculado a ningún local"}
    """
    try:
        # Obtener el usuario para verificar su id_local
        usuario = db_session.query(Usuario).filter(Usuario.id == user_id).first()
        
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 404
            
        if not usuario.id_local:
            return jsonify({'error': 'Usuario no vinculado a ningún local'}), 404
        
        # Obtener todas las reservas del local
        reservas = db_session.query(Reserva)\
            .options(
                joinedload(Reserva.usuario),
                joinedload(Reserva.reservas_mesa).joinedload(ReservaMesa.mesa)
            )\
            .filter(Reserva.id_local == usuario.id_local)\
            .order_by(Reserva.fecha_reserva.desc(), Reserva.hora_reserva.desc())\
            .all()
        
        reservas_lista = []
        for reserva in reservas:
            # Obtener nombres de mesas
            mesas_nombres = [rm.mesa.nombre for rm in reserva.reservas_mesa if rm.mesa]
            mesa_str = ", ".join(mesas_nombres) if mesas_nombres else "Sin asignar"
            
            # Calcular número de personas basado en capacidad de mesas (aproximado)
            total_personas = sum(rm.mesa.capacidad for rm in reserva.reservas_mesa if rm.mesa) if reserva.reservas_mesa else 2
            
            # Calcular tiempo desde la creación
            tiempo_transcurrido = "Reciente"
            if reserva.creado_el:
                delta = datetime.now(reserva.creado_el.tzinfo) - reserva.creado_el
                if delta.days > 0:
                    tiempo_transcurrido = f"Hace {delta.days} día{'s' if delta.days > 1 else ''}"
                elif delta.seconds // 3600 > 0:
                    horas = delta.seconds // 3600
                    tiempo_transcurrido = f"Hace {horas} hora{'s' if horas > 1 else ''}"
                else:
                    minutos = delta.seconds // 60
                    tiempo_transcurrido = f"Hace {minutos} minuto{'s' if minutos > 1 else ''}"
            
            reservas_lista.append({
                'id': str(reserva.id),
                'clientName': reserva.usuario.nombre if reserva.usuario else 'Cliente Anónimo',
                'clientEmail': reserva.usuario.correo if reserva.usuario else 'Sin email',
                'date': reserva.fecha_reserva.strftime('%Y-%m-%d') if reserva.fecha_reserva else None,
                'time': reserva.hora_reserva.strftime('%H:%M') if reserva.hora_reserva else None,
                'pax': total_personas,
                'status': reserva.estado.value if reserva.estado else 'pendiente',
                'table': mesa_str,
                'requestDate': tiempo_transcurrido
            })
        
        return jsonify(reservas_lista), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Error al obtener las reservas del local'}), 500


@reservas_bp.route('/<int:id_reserva>/estado', methods=['PUT'])
@requerir_auth
def actualizar_estado_reserva(user_id, user_rol, id_reserva):
    """
    Actualizar el estado de una reserva
    
    Headers:
        Authorization: Bearer {token}
        
    Body:
        {
            "estado": "confirmada" | "cancelada" | "pendiente" | "completada"
        }
        
    Response 200:
        {
            "success": true,
            "message": "Estado de reserva actualizado",
            "reserva": {
                "id": 1,
                "estado": "confirmada"
            }
        }
        
    Response 403:
        {"error": "No tienes permiso para modificar esta reserva"}
        
    Response 404:
        {"error": "Reserva no encontrada"}
    """
    try:
        data = request.get_json()
        nuevo_estado = data.get('estado', '').lower()
        
        # Mapeo de strings a valores del enum
        estados_map = {
            'pendiente': EstadoReservaEnum.PENDIENTE,
            'confirmada': EstadoReservaEnum.CONFIRMADA,
            'rechazada': EstadoReservaEnum.RECHAZADA
        }
        
        # Validar estado
        if nuevo_estado not in estados_map:
            return jsonify({'error': f'Estado inválido. Debe ser uno de: {", ".join(estados_map.keys())}'}), 400
        
        # Obtener la reserva
        reserva = db_session.query(Reserva).filter(Reserva.id == id_reserva).first()
        
        if not reserva:
            return jsonify({'error': 'Reserva no encontrada'}), 404
        
        # Verificar que el usuario tenga acceso (debe ser del mismo local)
        usuario = db_session.query(Usuario).filter(Usuario.id == user_id).first()
        if not usuario or not usuario.id_local:
            return jsonify({'error': 'Usuario no vinculado a ningún local'}), 403
            
        if reserva.id_local != usuario.id_local:
            return jsonify({'error': 'No tienes permiso para modificar esta reserva'}), 403
        
        # Actualizar estado usando el enum correcto
        reserva.estado = estados_map[nuevo_estado]
        db_session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Reserva actualizada a estado: {nuevo_estado}',
            'reserva': {
                'id': reserva.id,
                'estado': reserva.estado.value
            }
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        db_session.rollback()
        return jsonify({'error': 'Error al actualizar el estado de la reserva'}), 500
