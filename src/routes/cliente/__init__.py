"""
Rutas de cliente para pedidos mediante QR
Prefix: /api/cliente/*
"""

from routes.cliente.pedidos import cliente_bp

__all__ = ["cliente_bp"]
