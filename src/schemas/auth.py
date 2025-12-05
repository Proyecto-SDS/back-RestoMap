"""
Schemas para autenticacion y usuarios.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator


class UsuarioBase(BaseModel):
    """Schema base de usuario"""

    nombre: str = Field(..., min_length=1)
    correo: EmailStr
    telefono: str | None = None


class UsuarioCreateSchema(UsuarioBase):
    """Schema para crear usuario"""

    contrasena: str = Field(..., min_length=6)
    id_rol: int = 2  # Por defecto: usuario normal


class UsuarioUpdateSchema(BaseModel):
    """Schema para actualizar usuario"""

    nombre: str | None = Field(None, min_length=1)
    telefono: str | None = None
    correo: EmailStr | None = None

    # pyrefly: ignore  # bad-argument-type
    @field_validator("telefono")
    @classmethod
    def validar_telefono(cls, v: str | None) -> str | None:
        if v is None:
            return v
        # Limpiar telefono
        telefono_limpio = v.replace("+56", "").replace(" ", "").replace("-", "")
        if not telefono_limpio.isdigit() or len(telefono_limpio) != 9:
            msg = "Telefono invalido. Debe tener 9 digitos"
            raise ValueError(msg)
        return telefono_limpio


class UsuarioResponseSchema(UsuarioBase):
    """Schema de respuesta de usuario (sin contrasena)"""

    id: int
    id_rol: int | None = None
    creado_el: datetime | None = None

    class Config:
        from_attributes = True


class UsuarioSchema(UsuarioBase):
    """Schema completo de usuario (legacy)"""

    id: int | None = None
    id_rol: int | None = None

    class Config:
        from_attributes = True


class LoginSchema(BaseModel):
    """Schema para login"""

    correo: EmailStr
    contrasena: str = Field(..., min_length=1)
    tipo_login: Literal["persona", "empresa"] = "persona"


class RegisterSchema(BaseModel):
    """Schema para registro de usuario"""

    nombre: str = Field(..., min_length=1)
    correo: EmailStr
    contrasena: str = Field(..., min_length=6)
    telefono: str

    # pyrefly: ignore  # bad-argument-type
    @field_validator("telefono")
    @classmethod
    def validar_telefono(cls, v: str) -> str:
        # Limpiar telefono
        telefono_limpio = v.replace("+56", "").replace(" ", "").replace("-", "")
        if not telefono_limpio.isdigit() or len(telefono_limpio) != 9:
            msg = "Telefono invalido. Debe tener 9 digitos"
            raise ValueError(msg)
        return telefono_limpio


class ProfileUpdateSchema(BaseModel):
    """Schema para actualizar perfil"""

    nombre: str | None = Field(None, min_length=1)
    telefono: str | None = None

    # pyrefly: ignore  # bad-argument-type
    @field_validator("telefono")
    @classmethod
    def validar_telefono(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return None
        telefono_limpio = v.replace("+56", "").replace(" ", "").replace("-", "")
        if not telefono_limpio.isdigit() or len(telefono_limpio) != 9:
            msg = "Telefono invalido. Debe tener 9 digitos"
            raise ValueError(msg)
        return telefono_limpio


class RolSchema(BaseModel):
    """Schema de rol"""

    id: int | None = None
    nombre: str

    class Config:
        from_attributes = True
