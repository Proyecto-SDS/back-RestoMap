"""
Módulo de excepciones personalizadas del sistema RestoMap.
"""

from .base import AppError, BusinessLogicError, DatabaseError, ValidationError
from .http import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    HTTPError,
    InternalServerError,
    NotFoundError,
    TooManyRequestsError,
    UnauthorizedError,
    UnprocessableEntityError,
)

__all__ = [
    "AppError",
    "BadRequestError",
    "BusinessLogicError",
    "ConflictError",
    "DatabaseError",
    "ForbiddenError",
    "HTTPError",
    "InternalServerError",
    "NotFoundError",
    "TooManyRequestsError",
    "UnauthorizedError",
    "UnprocessableEntityError",
    "ValidationError",
]
