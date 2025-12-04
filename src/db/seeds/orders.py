import logging
from datetime import datetime, timedelta

from models import (
    Cuenta,
    Encomienda,
    EncomiendaCuenta,
    EstadoEncomiendaEnum,
    EstadoPagoEnum,
    EstadoPedido,
    EstadoPedidoEnum,
    MetodoPagoEnum,
    Pago,
    Pedido,
)

logger = logging.getLogger(__name__)


def create_orders(db):
    # ============ Pedidos ============
    logger.info("  → Insertando Pedidos de ejemplo...")
    if db.query(Pedido).count() == 0:
        # Primero crear QRs temporales para los pedidos
        from models import QRDinamico

        qr1 = QRDinamico(
            id_mesa=3,
            id_usuario=2,
            codigo="QR-SEED-M3-U2-TEMP",
            expiracion=datetime.now() + timedelta(hours=4),
            activo=True,
        )
        qr2 = QRDinamico(
            id_mesa=4,
            id_usuario=3,
            codigo="QR-SEED-M4-U3-TEMP",
            expiracion=datetime.now() + timedelta(hours=4),
            activo=True,
        )
        qr3 = QRDinamico(
            id_mesa=7,
            id_usuario=2,
            codigo="QR-SEED-M7-U2-TEMP",
            expiracion=datetime.now() + timedelta(hours=4),
            activo=True,
        )
        db.add_all([qr1, qr2, qr3])
        db.commit()

        # Pedido iniciado
        pedido1 = Pedido(
            id_local=1,
            id_mesa=3,
            id_usuario=2,
            id_qr=qr1.id,
            creado_por=4,
            estado=EstadoPedidoEnum.INICIADO,
            total=14000,
        )
        # Pedido en proceso
        pedido2 = Pedido(
            id_local=1,
            id_mesa=4,
            id_usuario=3,
            id_qr=qr2.id,
            creado_por=4,
            estado=EstadoPedidoEnum.EN_PROCESO,
            total=25300,
        )
        # Pedido completado (histórico)
        pedido3 = Pedido(
            id_local=2,
            id_mesa=7,
            id_usuario=2,
            id_qr=qr3.id,
            creado_por=4,
            estado=EstadoPedidoEnum.COMPLETADO,
            total=18500,
            creado_el=datetime.now() - timedelta(days=1),
        )
        db.add_all([pedido1, pedido2, pedido3])
        db.commit()

        # Vincular QRs con pedidos
        qr1.id_pedido = pedido1.id
        qr2.id_pedido = pedido2.id
        qr3.id_pedido = pedido3.id
        db.commit()

        # Cuentas para pedido 1
        db.add_all(
            [
                Cuenta(
                    id_pedido=pedido1.id,
                    id_producto=1,
                    creado_por=2,
                    cantidad=2,
                    observaciones="Sin cebolla",
                ),
                Cuenta(
                    id_pedido=pedido1.id,
                    id_producto=5,
                    creado_por=2,
                    cantidad=1,
                    observaciones="",
                ),
            ]
        )
        # Cuentas para pedido 2
        db.add_all(
            [
                Cuenta(
                    id_pedido=pedido2.id,
                    id_producto=2,
                    creado_por=3,
                    cantidad=1,
                    observaciones="Término medio",
                ),
                Cuenta(
                    id_pedido=pedido2.id,
                    id_producto=3,
                    creado_por=3,
                    cantidad=2,
                    observaciones="",
                ),
            ]
        )
        # Cuentas para pedido 3
        db.add_all(
            [
                Cuenta(
                    id_pedido=pedido3.id,
                    id_producto=6,
                    creado_por=2,
                    cantidad=3,
                    observaciones="",
                ),
                Cuenta(
                    id_pedido=pedido3.id,
                    id_producto=8,
                    creado_por=2,
                    cantidad=2,
                    observaciones="",
                ),
            ]
        )
        db.commit()

        # Estados de pedido (historial de cambios)
        db.add_all(
            [
                EstadoPedido(
                    id_pedido=pedido1.id,
                    estado=EstadoPedidoEnum.INICIADO,
                    creado_por=4,
                ),
                EstadoPedido(
                    id_pedido=pedido2.id,
                    estado=EstadoPedidoEnum.INICIADO,
                    creado_por=4,
                    creado_el=datetime.now() - timedelta(minutes=30),
                ),
                EstadoPedido(
                    id_pedido=pedido2.id,
                    estado=EstadoPedidoEnum.RECEPCION,
                    creado_por=5,
                    creado_el=datetime.now() - timedelta(minutes=20),
                ),
                EstadoPedido(
                    id_pedido=pedido2.id,
                    estado=EstadoPedidoEnum.EN_PROCESO,
                    creado_por=5,
                    creado_el=datetime.now() - timedelta(minutes=15),
                ),
                EstadoPedido(
                    id_pedido=pedido3.id,
                    estado=EstadoPedidoEnum.COMPLETADO,
                    creado_por=4,
                    creado_el=datetime.now() - timedelta(days=1),
                ),
            ]
        )
        db.commit()
        logger.info("    ✓ Pedidos, Cuentas y Estados insertados")

        # ============ Pagos ============
        logger.info("  → Insertando Pagos de ejemplo...")
        # Pago del pedido cerrado
        db.add(
            Pago(
                id_pedido=3,
                creado_por=4,
                metodo=MetodoPagoEnum.CREDITO,
                estado=EstadoPagoEnum.COBRADO,
                monto=18500,
                creado_el=datetime.now() - timedelta(days=1),
            )
        )
        # Pago pendiente para pedido en preparacion
        db.add(
            Pago(
                id_pedido=2,
                creado_por=4,
                metodo=MetodoPagoEnum.EFECTIVO,
                estado=EstadoPagoEnum.PENDIENTE,
                monto=25300,
            )
        )
        db.commit()
        logger.info("    ✓ Pagos insertados")

        # ============ Encomiendas ============
        logger.info("  → Insertando Encomiendas de ejemplo...")
        # Intentamos usar el pedido 2 si existe, sino buscamos uno
        pedido_enc = db.query(Pedido).filter(Pedido.id == 2).first()
        if not pedido_enc:
            pedido_enc = db.query(Pedido).first()

        if pedido_enc:
            enc1 = Encomienda(
                id_pedido=pedido_enc.id, estado=EstadoEncomiendaEnum.EN_PREPARACION
            )
            db.add(enc1)
            db.commit()

            # Vincular cuenta con encomienda
            cuenta_enc = (
                db.query(Cuenta).filter(Cuenta.id_pedido == pedido_enc.id).first()
            )
            if cuenta_enc:
                db.add(EncomiendaCuenta(id_cuenta=cuenta_enc.id, id_encomienda=enc1.id))
                db.commit()

            logger.info("    ✓ Encomiendas insertadas")
        else:
            logger.info("    No se pudo insertar Encomienda (no hay pedidos)")

    else:
        logger.info("    Pedidos ya existen")
