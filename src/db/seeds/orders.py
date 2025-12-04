import logging
from datetime import datetime, timedelta
from models import (
    Pedido, Cuenta, EstadoPedido, Pago, Encomienda, EncomiendaCuenta,
    EstadoPedidoEnum, EstadoPagoEnum, MetodoPagoEnum, EstadoEncomiendaEnum
)

logger = logging.getLogger(__name__)

def create_orders(db):
    # ============ Pedidos ============
    logger.info("  → Insertando Pedidos de ejemplo...")
    if db.query(Pedido).count() == 0:
        # Pedido abierto
        pedido1 = Pedido(
            local_id=1, mesa_id=3, usuario_id=2,
            estado=EstadoPedidoEnum.ABIERTO, total=14000
        )
        # Pedido en preparacion
        pedido2 = Pedido(
            local_id=1, mesa_id=4, usuario_id=3,
            estado=EstadoPedidoEnum.EN_PREPARACION, total=25300
        )
        # Pedido cerrado (historico)
        pedido3 = Pedido(
            local_id=2, mesa_id=7, usuario_id=2,
            estado=EstadoPedidoEnum.CERRADO, total=18500,
            creado_el=datetime.now() - timedelta(days=1)
        )
        db.add_all([pedido1, pedido2, pedido3])
        db.commit()
        
        # Cuentas para pedido 1
        db.add_all([
            Cuenta(id_pedido=pedido1.id, id_producto=1, cantidad=2, observaciones="Sin cebolla"),
            Cuenta(id_pedido=pedido1.id, id_producto=5, cantidad=1, observaciones=""),
        ])
        # Cuentas para pedido 2
        db.add_all([
            Cuenta(id_pedido=pedido2.id, id_producto=2, cantidad=1, observaciones="Término medio"),
            Cuenta(id_pedido=pedido2.id, id_producto=3, cantidad=2, observaciones=""),
        ])
        # Cuentas para pedido 3
        db.add_all([
            Cuenta(id_pedido=pedido3.id, id_producto=6, cantidad=3, observaciones=""),
            Cuenta(id_pedido=pedido3.id, id_producto=8, cantidad=2, observaciones=""),
        ])
        db.commit()
        
        # Estados de pedido
        db.add_all([
            EstadoPedido(pedido_id=pedido1.id, estado=EstadoPedidoEnum.ABIERTO, creado_por=4),
            EstadoPedido(pedido_id=pedido2.id, estado=EstadoPedidoEnum.ABIERTO, creado_por=4,
                       creado_el=datetime.now() - timedelta(minutes=30)),
            EstadoPedido(pedido_id=pedido2.id, estado=EstadoPedidoEnum.EN_PREPARACION, creado_por=5,
                       creado_el=datetime.now() - timedelta(minutes=15)),
            EstadoPedido(pedido_id=pedido3.id, estado=EstadoPedidoEnum.CERRADO, creado_por=4,
                       creado_el=datetime.now() - timedelta(days=1)),
        ])
        db.commit()
        logger.info("    ✓ Pedidos, Cuentas y Estados insertados")

        # ============ Pagos ============
        logger.info("  → Insertando Pagos de ejemplo...")
        # Pago del pedido cerrado
        db.add(Pago(
            pedido_id=3, metodo=MetodoPagoEnum.CREDITO,
            estado=EstadoPagoEnum.COBRADO, monto=18500,
            creado_el=datetime.now() - timedelta(days=1)
        ))
        # Pago pendiente para pedido en preparacion
        db.add(Pago(
            pedido_id=2, metodo=MetodoPagoEnum.EFECTIVO,
            estado=EstadoPagoEnum.PENDIENTE, monto=25300
        ))
        db.commit()
        logger.info("    ✓ Pagos insertados")

        # ============ Encomiendas ============
        logger.info("  → Insertando Encomiendas de ejemplo...")
        # Intentamos usar el pedido 2 si existe, sino buscamos uno
        pedido_enc = db.query(Pedido).filter(Pedido.id == 2).first()
        if not pedido_enc:
             pedido_enc = db.query(Pedido).first()
        
        if pedido_enc:
            enc1 = Encomienda(id_pedido=pedido_enc.id, estado=EstadoEncomiendaEnum.EN_PREPARACION)
            db.add(enc1)
            db.commit()
            
            # Vincular cuenta con encomienda
            cuenta_enc = db.query(Cuenta).filter(Cuenta.id_pedido == pedido_enc.id).first()
            if cuenta_enc:
                db.add(EncomiendaCuenta(id_cuenta=cuenta_enc.id, id_encomienda=enc1.id))
                db.commit()
            
            logger.info("    ✓ Encomiendas insertadas")
        else:
            logger.info("    No se pudo insertar Encomienda (no hay pedidos)")

    else:
        logger.info("    Pedidos ya existen")
