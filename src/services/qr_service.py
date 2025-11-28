"""
Servicio para generar códigos QR dinámicos para reservas y pedidos
"""
import qrcode
import base64
from io import BytesIO
from datetime import datetime, timedelta
import secrets
from typing import Optional, Tuple

from database import db_session
from models import QRDinamico, Reserva, Pedido, Mesa


def generar_codigo_unico() -> str:
    """
    Genera un código único alfanumérico para el QR
    Formato: QR-XXXXXXXXXXXXXXXX (8 bytes = 16 caracteres hex)
    """
    codigo_hex = secrets.token_hex(8)
    return f"QR-{codigo_hex.upper()}"


def generar_qr_imagen(data: str, size: int = 10) -> str:
    """
    Genera una imagen QR y la retorna como base64
    
    Args:
        data: Datos a codificar en el QR
        size: Tamaño del QR (box_size)
    
    Returns:
        String base64 de la imagen PNG
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=size,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convertir a base64
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"


def crear_qr_reserva(
    id_reserva: int,
    id_mesa: int,
    minutos_tolerancia: int = 10
) -> Tuple[str, str]:
    """
    Crea un QR dinámico para una reserva
    
    Args:
        id_reserva: ID de la reserva
        id_mesa: ID de la mesa asociada
        minutos_tolerancia: Minutos de tolerancia después de la hora de reserva (default: 10 minutos)
    
    Returns:
        Tupla (codigo, qr_base64)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"[QR Service] Iniciando creación de QR para reserva {id_reserva}")
    
    # Verificar que la reserva existe
    reserva = db_session.query(Reserva).filter(Reserva.id == id_reserva).first()
    if not reserva:
        raise ValueError(f"Reserva con ID {id_reserva} no encontrada")
    
    logger.info(f"[QR Service] Reserva encontrada: fecha={reserva.fecha_reserva}, hora={reserva.hora_reserva}")
    
    # Verificar que la mesa existe
    mesa = db_session.query(Mesa).filter(Mesa.id == id_mesa).first()
    if not mesa:
        raise ValueError(f"Mesa con ID {id_mesa} no encontrada")
    
    logger.info(f"[QR Service] Mesa encontrada: {mesa.nombre}")
    
    # Generar código único
    codigo = generar_codigo_unico()
    logger.info(f"[QR Service] Código generado: {codigo}")
    
    # Calcular fecha de expiración: fecha+hora de reserva + tolerancia
    # Combinar fecha y hora de la reserva
    fecha_hora_reserva = datetime.combine(reserva.fecha_reserva, reserva.hora_reserva)
    # Agregar los minutos de tolerancia
    expiracion = fecha_hora_reserva + timedelta(minutes=minutos_tolerancia)
    logger.info(f"[QR Service] Expiración calculada: {expiracion}")
    
    # Crear registro en la base de datos
    qr_dinamico = QRDinamico(
        id_mesa=id_mesa,
        id_reserva=id_reserva,
        id_pedido=None,
        codigo=codigo,
        expiracion=expiracion,
        activo=True
    )
    
    db_session.add(qr_dinamico)
    db_session.commit()
    logger.info(f"[QR Service] Registro guardado en BD con ID: {qr_dinamico.id}")
    
    # Generar imagen QR con el código
    # Incluir información útil en el QR
    qr_data = {
        "tipo": "reserva",
        "codigo": codigo,
        "reserva_id": id_reserva,
        "mesa_id": id_mesa,
        "local_id": reserva.id_local,
        "fecha": reserva.fecha_reserva.isoformat() if reserva.fecha_reserva else None,
        "hora": reserva.hora_reserva.strftime("%H:%M") if reserva.hora_reserva else None
    }
    
    logger.info(f"[QR Service] Datos para QR: {qr_data}")
    
    # Convertir a string para el QR (JSON simple)
    import json
    qr_string = json.dumps(qr_data)
    
    logger.info(f"[QR Service] Generando imagen QR...")
    qr_base64 = generar_qr_imagen(qr_string)
    logger.info(f"[QR Service] Imagen generada, tamaño: {len(qr_base64)} caracteres")
    
    return codigo, qr_base64


def crear_qr_pedido(
    id_pedido: int,
    id_mesa: int,
    dias_expiracion: int = 1
) -> Tuple[str, str]:
    """
    Crea un QR dinámico para un pedido
    
    Args:
        id_pedido: ID del pedido
        id_mesa: ID de la mesa asociada
        dias_expiracion: Días hasta que expire el QR (default: 1 día)
    
    Returns:
        Tupla (codigo, qr_base64)
    """
    # Verificar que el pedido existe
    pedido = db_session.query(Pedido).filter(Pedido.id == id_pedido).first()
    if not pedido:
        raise ValueError(f"Pedido con ID {id_pedido} no encontrado")
    
    # Verificar que la mesa existe
    mesa = db_session.query(Mesa).filter(Mesa.id == id_mesa).first()
    if not mesa:
        raise ValueError(f"Mesa con ID {id_mesa} no encontrada")
    
    # Generar código único
    codigo = generar_codigo_unico()
    
    # Calcular fecha de expiración
    expiracion = datetime.utcnow() + timedelta(days=dias_expiracion)
    
    # Crear registro en la base de datos
    qr_dinamico = QRDinamico(
        id_mesa=id_mesa,
        id_pedido=id_pedido,
        id_reserva=None,
        codigo=codigo,
        expiracion=expiracion,
        activo=True
    )
    
    db_session.add(qr_dinamico)
    db_session.commit()
    
    # Generar imagen QR con el código
    import json
    qr_data = {
        "tipo": "pedido",
        "codigo": codigo,
        "pedido_id": id_pedido,
        "mesa_id": id_mesa,
        "local_id": pedido.local_id
    }
    
    qr_string = json.dumps(qr_data)
    qr_base64 = generar_qr_imagen(qr_string)
    
    return codigo, qr_base64


def validar_qr(codigo: str) -> Optional[QRDinamico]:
    """
    Valida un código QR y verifica que esté activo y no haya expirado
    
    Args:
        codigo: Código del QR a validar
    
    Returns:
        QRDinamico si es válido, None si no es válido
    """
    qr = db_session.query(QRDinamico).filter(QRDinamico.codigo == codigo).first()
    
    if not qr:
        return None
    
    # Verificar que esté activo
    if not qr.activo:
        return None
    
    # Verificar que no haya expirado
    if qr.expiracion and qr.expiracion < datetime.utcnow():
        return None
    
    return qr


def desactivar_qr(codigo: str) -> bool:
    """
    Desactiva un código QR
    
    Args:
        codigo: Código del QR a desactivar
    
    Returns:
        True si se desactivó exitosamente, False si no se encontró
    """
    qr = db_session.query(QRDinamico).filter(QRDinamico.codigo == codigo).first()
    
    if not qr:
        return False
    
    qr.activo = False
    db_session.commit()
    
    return True
