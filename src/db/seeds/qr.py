import logging
from datetime import datetime, timedelta
from models import QRDinamico, Pedido, Reserva, ReservaMesa, EstadoPedidoEnum, EstadoReservaEnum

logger = logging.getLogger(__name__)

def create_qrs(db):
    # ============ QR Dinamicos ============
    logger.info("  → Insertando QR Dinamicos de ejemplo...")
    
    if db.query(QRDinamico).count() > 0:
        logger.info("    QR Dinamicos ya existen")
        return

    qrs_to_add = []
    
    # 1. QR para un Pedido Abierto
    pedido_abierto = db.query(Pedido).filter(
        Pedido.estado == EstadoPedidoEnum.ABIERTO,
        Pedido.mesa_id.isnot(None)
    ).first()
    
    if pedido_abierto:
        qrs_to_add.append(QRDinamico(
            id_mesa=pedido_abierto.mesa_id,
            id_pedido=pedido_abierto.id,
            id_reserva=None,
            codigo=f"QR-P{pedido_abierto.id}-M{pedido_abierto.mesa_id}-AUTO",
            expiracion=datetime.now() + timedelta(hours=4),
            activo=True
        ))
    
    # 2. QR para una Reserva Confirmada
    reserva_confirmada = db.query(Reserva).filter(
        Reserva.estado == EstadoReservaEnum.CONFIRMADA
    ).first()
    
    if reserva_confirmada:
        reserva_mesa = db.query(ReservaMesa).filter(
            ReservaMesa.id_reserva == reserva_confirmada.id
        ).first()
        
        if reserva_mesa:
            qrs_to_add.append(QRDinamico(
                id_mesa=reserva_mesa.id_mesa,
                id_pedido=None,
                id_reserva=reserva_confirmada.id,
                codigo=f"QR-R{reserva_confirmada.id}-M{reserva_mesa.id_mesa}-AUTO",
                expiracion=datetime.now() + timedelta(days=1),
                activo=True
            ))

    # 3. QR para un Pedido en Preparacion
    pedido_prep = db.query(Pedido).filter(
        Pedido.estado == EstadoPedidoEnum.EN_PREPARACION,
        Pedido.mesa_id.isnot(None)
    ).first()

    if pedido_prep:
            qrs_to_add.append(QRDinamico(
            id_mesa=pedido_prep.mesa_id,
            id_pedido=pedido_prep.id,
            id_reserva=None,
            codigo=f"QR-P{pedido_prep.id}-M{pedido_prep.mesa_id}-PREP",
            expiracion=datetime.now() + timedelta(hours=4),
            activo=True
        ))

    if qrs_to_add:
        db.add_all(qrs_to_add)
        db.commit()
        logger.info(f"    ✓ {len(qrs_to_add)} QR Dinamicos insertados correctamente")
    else:
        logger.info("    No se pudieron generar QRs (faltan pedidos/reservas base)")
