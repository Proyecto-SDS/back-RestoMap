"""
Rutas de opiniones
Endpoints: /api/opiniones/*
"""
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import joinedload
from datetime import datetime

from database import db_session
from models import Opinion, Local, Usuario
from utils.jwt_helper import requerir_auth

opiniones_bp = Blueprint('opiniones', __name__, url_prefix='/api/opiniones')


@opiniones_bp.route('/', methods=['POST'])
@requerir_auth
def crear_opinion(user_id, user_rol):
    """
    Crear nueva opinion para un local
    
    Headers:
        Authorization: Bearer {token}
        
    Body:
        {
            "localId": "1",
            "puntuacion": 4.5,
            "comentario": "Excelente comida y servicio"
        }
        
    Response 201:
        {
            "success": true,
            "message": "Opinion creada exitosamente",
            "opinion": {
                "id": 1,
                "localId": "1",
                "usuario": "Juan Pérez",
                "puntuacion": 4.5,
                "comentario": "Excelente comida...",
                "fecha": "2024-11-24T12:00:00"
            }
        }
        
    Response 400:
        {"error": "localId, puntuacion y comentario son requeridos"}
        {"error": "La puntuacion debe estar entre 1 y 5"}
        {"error": "El comentario debe tener entre 10 y 500 caracteres"}
        {"error": "Ya tienes una opinion para este local"}
        
    Response 404:
        {"error": "Local no encontrado"}
    """
    try:
        data = request.get_json()
        
        local_id = data.get('localId')
        puntuacion = data.get('puntuacion')
        comentario = data.get('comentario', '').strip()
        
        # Validar campos requeridos
        if not local_id or puntuacion is None or not comentario:
            return jsonify({'error': 'localId, puntuacion y comentario son requeridos'}), 400
        
        # Convertir local_id a int
        try:
            local_id = int(local_id)
        except ValueError:
            return jsonify({'error': 'localId debe ser un número'}), 400
        
        # Validar puntuacion
        try:
            puntuacion = float(puntuacion)
            if puntuacion < 1 or puntuacion > 5:
                return jsonify({'error': 'La puntuacion debe estar entre 1 y 5'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Puntuacion invalida'}), 400
        
        # Validar comentario
        if len(comentario) < 10 or len(comentario) > 500:
            return jsonify({'error': 'El comentario debe tener entre 10 y 500 caracteres'}), 400
        
        # Verificar que el local existe
        local = db_session.query(Local).filter(Local.id == local_id).first()
        if not local:
            return jsonify({'error': 'Local no encontrado'}), 404
        
        # Verificar que el usuario no tenga ya una opinion para este local
        opinion_existente = db_session.query(Opinion)\
            .filter(
                Opinion.id_usuario == user_id,
                Opinion.id_local == local_id,
                Opinion.eliminado_el.is_(None)
            )\
            .first()
        
        if opinion_existente:
            return jsonify({'error': 'Ya tienes una opinion para este local'}), 400
        
        # Crear nueva opinion
        nueva_opinion = Opinion(
            id_usuario=user_id,
            id_local=local_id,
            puntuacion=puntuacion,
            comentario=comentario,
            creado_el=datetime.utcnow()
        )
        
        db_session.add(nueva_opinion)
        db_session.commit()
        db_session.refresh(nueva_opinion)
        
        # Obtener usuario para respuesta
        usuario = db_session.query(Usuario).filter(Usuario.id == user_id).first()
        usuario_nombre = usuario.nombre if usuario else 'Usuario'
        
        return jsonify({
            'success': True,
            'message': 'Opinion creada exitosamente',
            'opinion': {
                'id': nueva_opinion.id,
                'localId': str(local_id),
                'usuario': usuario_nombre,
                # pyrefly: ignore [bad-argument-type]
                'puntuacion': float(nueva_opinion.puntuacion),
                'comentario': nueva_opinion.comentario,
                'fecha': nueva_opinion.creado_el.isoformat()
            }
        }), 201
        
    except Exception as e:
        db_session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Error al crear la opinion'}), 500


@opiniones_bp.route('/mis-opiniones', methods=['GET'])
@requerir_auth
def obtener_mis_opiniones(user_id, user_rol):
    """
    Obtener todas las opiniones del usuario autenticado
    
    Headers:
        Authorization: Bearer {token}
        
    Response 200:
        {
            "opiniones": [
                {
                    "id": 1,
                    "localId": "1",
                    "localNombre": "El Gran Sabor",
                    "puntuacion": 4.5,
                    "comentario": "Excelente comida...",
                    "fecha": "2024-11-24T12:00:00"
                }
            ]
        }
    """
    try:
        opiniones = db_session.query(Opinion)\
            .options(joinedload(Opinion.local))\
            .filter(
                Opinion.id_usuario == user_id,
                Opinion.eliminado_el.is_(None)
            )\
            .order_by(Opinion.creado_el.desc())\
            .all()
        
        opiniones_lista = []
        for opinion in opiniones:
            opiniones_lista.append({
                'id': opinion.id,
                'localId': str(opinion.id_local),
                'localNombre': opinion.local.nombre if opinion.local else 'Local',
                # pyrefly: ignore [bad-argument-type]
                'puntuacion': float(opinion.puntuacion),
                'comentario': opinion.comentario,
                'fecha': opinion.creado_el.isoformat() if opinion.creado_el else None
            })
        
        return jsonify({'opiniones': opiniones_lista}), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Error al obtener las opiniones'}), 500


@opiniones_bp.route('/<int:local_id>/user', methods=['GET'])
@requerir_auth
def obtener_opinion_usuario(local_id, user_id, user_rol):
    """
    Obtener la opinion del usuario autenticado para un local especifico
    
    Headers:
        Authorization: Bearer {token}
        
    Response 200:
        {
            "id": 1,
            "localId": "1",
            "usuario": "Juan Pérez",
            "puntuacion": 4.5,
            "comentario": "Excelente comida...",
            "fecha": "2024-11-24T12:00:00"
        }
        
    Response 404:
        {"error": "No tienes opinion para este local"}
    """
    try:
        opinion = db_session.query(Opinion)\
            .options(joinedload(Opinion.usuario))\
            .filter(
                Opinion.id_usuario == user_id,
                Opinion.id_local == local_id,
                Opinion.eliminado_el.is_(None)
            )\
            .first()
        
        if not opinion:
            return jsonify({'error': 'No tienes opinion para este local'}), 404
        
        return jsonify({
            'id': opinion.id,
            'localId': str(local_id),
            'usuario': opinion.usuario.nombre if opinion.usuario else 'Usuario',
            # pyrefly: ignore [bad-argument-type]
            'puntuacion': float(opinion.puntuacion),
            'comentario': opinion.comentario,
            'fecha': opinion.creado_el.isoformat() if opinion.creado_el else None
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Error al obtener la opinion'}), 500
