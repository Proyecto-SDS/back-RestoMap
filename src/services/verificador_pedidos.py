"""
Servicio de verificación de pedidos para alertas en tiempo real.

Este servicio se activa cuando hay conexiones WebSocket activas en un local
y verifica periódicamente:
1. Pedidos expirados -> cancela y emite evento
2. Alertas TERMINADO -> 5min, 10min sin servir
3. Alertas SERVIDO -> 15min, 10min, 5min antes de expirar
4. Urgencia Kanban -> >30min en RECEPCION
"""

import threading
from collections.abc import Callable
from datetime import datetime
from zoneinfo import ZoneInfo

from config import get_logger

logger = get_logger(__name__)

# Zona horaria de Chile (consistente con Docker y BD)
TIMEZONE_CHILE = ZoneInfo("America/Santiago")


def _ahora() -> datetime:
    """Retorna la fecha/hora actual con timezone de Chile."""
    return datetime.now(TIMEZONE_CHILE)


# Diccionario de timers activos por local
_verificadores_activos: dict[int, threading.Timer] = {}

# Diccionario para rastrear alertas ya enviadas (evitar spam)
_alertas_enviadas: dict[str, datetime] = {}

# Intervalo de verificación en segundos
INTERVALO_VERIFICACION = 30


def _generar_key_alerta(pedido_id: int, tipo_alerta: str) -> str:
    """Genera una key única para rastrear alertas enviadas."""
    return f"{pedido_id}_{tipo_alerta}"


def _alerta_ya_enviada(pedido_id: int, tipo_alerta: str) -> bool:
    """Verifica si una alerta ya fue enviada recientemente (últimos 5 min)."""
    key = _generar_key_alerta(pedido_id, tipo_alerta)
    if key in _alertas_enviadas:
        tiempo_desde = (_ahora() - _alertas_enviadas[key]).total_seconds()
        # No reenviar si fue hace menos de 5 minutos
        return tiempo_desde < 300
    return False


def _marcar_alerta_enviada(pedido_id: int, tipo_alerta: str):
    """Marca una alerta como enviada."""
    key = _generar_key_alerta(pedido_id, tipo_alerta)
    _alertas_enviadas[key] = _ahora()


def _limpiar_alertas_antiguas():
    """Limpia alertas enviadas hace más de 30 minutos."""
    ahora = _ahora()
    keys_a_eliminar = [
        key
        for key, tiempo in _alertas_enviadas.items()
        if (ahora - tiempo).total_seconds() > 1800
    ]
    for key in keys_a_eliminar:
        del _alertas_enviadas[key]


def verificar_pedidos_local(local_id: int, callback_continuar: Callable[[], bool]):
    """
    Verifica pedidos de un local y emite alertas.

    Args:
        local_id: ID del local a verificar
        callback_continuar: Función que retorna True si debe seguir verificando
    """
    from sqlalchemy import select
    from sqlalchemy.orm import joinedload

    from database import get_session
    from models import EstadoMesaEnum, EstadoPedidoEnum, Pedido
    from websockets.emitters import (
        emit_alerta_pedido,
        emit_mesa_actualizada,
        emit_pedido_expirado,
        emit_urgencia_kanban,
    )

    # Verificar si debe continuar
    if not callback_continuar():
        logger.debug(f"[Verificador] Local {local_id}: Detenido (sin conexiones)")
        return

    logger.debug(f"[Verificador] Local {local_id}: Ejecutando verificación...")

    db = get_session()
    try:
        ahora = _ahora()

        # Obtener pedidos activos del local
        stmt = (
            select(Pedido)
            .options(joinedload(Pedido.mesa))
            .where(
                Pedido.id_local == local_id,
                Pedido.estado.notin_(
                    [EstadoPedidoEnum.COMPLETADO, EstadoPedidoEnum.CANCELADO]
                ),
            )
        )
        pedidos = db.execute(stmt).scalars().unique().all()

        for pedido in pedidos:
            mesa_nombre = (
                pedido.mesa.nombre if pedido.mesa else f"Mesa {pedido.id_mesa}"
            )
            mesa_id = pedido.id_mesa

            # 1. VERIFICAR EXPIRACIÓN
            if pedido.expiracion and pedido.expiracion < ahora:
                # Pedido expirado - cancelar
                pedido.estado = EstadoPedidoEnum.CANCELADO
                db.commit()

                # Liberar mesa
                if pedido.mesa:
                    pedido.mesa.estado = EstadoMesaEnum.DISPONIBLE
                    db.commit()
                    emit_mesa_actualizada(local_id, mesa_id, "disponible")

                emit_pedido_expirado(local_id, pedido.id, mesa_id, mesa_nombre)
                logger.info(
                    f"[Verificador] Pedido {pedido.id} EXPIRADO - Mesa {mesa_nombre}"
                )
                continue

            # 2. ALERTAS ESTADO TERMINADO (5min, 10min sin servir)
            if pedido.estado == EstadoPedidoEnum.TERMINADO:
                # Calcular tiempo desde que está en TERMINADO
                tiempo_terminado = pedido.actualizado_el or pedido.creado_el
                if tiempo_terminado:
                    minutos_esperando = (ahora - tiempo_terminado).total_seconds() / 60

                    if minutos_esperando >= 10 and not _alerta_ya_enviada(
                        pedido.id, "terminado_10min"
                    ):
                        emit_alerta_pedido(
                            local_id,
                            pedido.id,
                            mesa_id,
                            mesa_nombre,
                            "terminado_10min",
                            f"ALERTA: Pedido {mesa_nombre} lleva 10+ min listo!",
                        )
                        _marcar_alerta_enviada(pedido.id, "terminado_10min")

                    elif minutos_esperando >= 5 and not _alerta_ya_enviada(
                        pedido.id, "terminado_5min"
                    ):
                        emit_alerta_pedido(
                            local_id,
                            pedido.id,
                            mesa_id,
                            mesa_nombre,
                            "terminado_5min",
                            f"Pedido {mesa_nombre} listo hace 5 min",
                        )
                        _marcar_alerta_enviada(pedido.id, "terminado_5min")

            # 3. ALERTAS ESTADO SERVIDO (15min, 10min, 5min antes de expirar)
            elif pedido.estado == EstadoPedidoEnum.SERVIDO and pedido.expiracion:
                minutos_restantes = (pedido.expiracion - ahora).total_seconds() / 60

                if minutos_restantes <= 5 and not _alerta_ya_enviada(
                    pedido.id, "servido_5min"
                ):
                    emit_alerta_pedido(
                        local_id,
                        pedido.id,
                        mesa_id,
                        mesa_nombre,
                        "servido_5min",
                        f"URGENTE: {mesa_nombre} expira en 5 min!",
                        int(minutos_restantes),
                    )
                    _marcar_alerta_enviada(pedido.id, "servido_5min")

                elif minutos_restantes <= 10 and not _alerta_ya_enviada(
                    pedido.id, "servido_10min"
                ):
                    emit_alerta_pedido(
                        local_id,
                        pedido.id,
                        mesa_id,
                        mesa_nombre,
                        "servido_10min",
                        f"Alerta: {mesa_nombre} expira en 10 min",
                        int(minutos_restantes),
                    )
                    _marcar_alerta_enviada(pedido.id, "servido_10min")

                elif minutos_restantes <= 15 and not _alerta_ya_enviada(
                    pedido.id, "servido_15min"
                ):
                    emit_alerta_pedido(
                        local_id,
                        pedido.id,
                        mesa_id,
                        mesa_nombre,
                        "servido_15min",
                        f"{mesa_nombre} expira en 15 min",
                        int(minutos_restantes),
                    )
                    _marcar_alerta_enviada(pedido.id, "servido_15min")

            # 4. URGENCIA KANBAN (>30min en RECEPCION)
            elif pedido.estado == EstadoPedidoEnum.RECEPCION:
                # Usar actualizado_el que indica cuando entró a RECEPCION
                # (si no existe, usar creado_el como fallback)
                tiempo_en_recepcion = pedido.actualizado_el or pedido.creado_el
                if tiempo_en_recepcion:
                    minutos_esperando = (
                        ahora - tiempo_en_recepcion
                    ).total_seconds() / 60

                    if minutos_esperando >= 30 and not _alerta_ya_enviada(
                        pedido.id, "urgencia_kanban"
                    ):
                        emit_urgencia_kanban(
                            local_id, pedido.id, mesa_nombre, int(minutos_esperando)
                        )
                        _marcar_alerta_enviada(pedido.id, "urgencia_kanban")

        # Limpiar alertas antiguas periódicamente
        _limpiar_alertas_antiguas()

    except Exception as e:
        logger.error(f"[Verificador] Error verificando local {local_id}: {e}")
    finally:
        db.close()

    # Programar siguiente verificación si debe continuar
    if callback_continuar():
        timer = threading.Timer(
            INTERVALO_VERIFICACION,
            verificar_pedidos_local,
            args=(local_id, callback_continuar),
        )
        timer.daemon = True
        timer.start()
        _verificadores_activos[local_id] = timer


def iniciar_verificador(local_id: int, callback_continuar: Callable[[], bool]):
    """Inicia el verificador para un local si no está corriendo."""
    if local_id in _verificadores_activos:
        # Ya hay un verificador activo
        return

    logger.info(f"[Verificador] Iniciando para local {local_id}")

    # Iniciar primera verificación
    timer = threading.Timer(
        INTERVALO_VERIFICACION,
        verificar_pedidos_local,
        args=(local_id, callback_continuar),
    )
    timer.daemon = True
    timer.start()
    _verificadores_activos[local_id] = timer


def detener_verificador(local_id: int):
    """Detiene el verificador para un local."""
    if local_id in _verificadores_activos:
        timer = _verificadores_activos.pop(local_id)
        timer.cancel()
        logger.info(f"[Verificador] Detenido para local {local_id}")
