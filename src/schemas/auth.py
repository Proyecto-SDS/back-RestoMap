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
    """Schema para registro de usuario (persona/cliente)"""

    nombre: str = Field(..., min_length=1)
    correo: EmailStr
    contrasena: str = Field(..., min_length=6)
    telefono: str
    acepta_terminos: bool = Field(..., description="Acepta terminos y condiciones B2C")

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

    # pyrefly: ignore  # bad-argument-type
    @field_validator("acepta_terminos")
    @classmethod
    def validar_terminos(cls, v: bool) -> bool:
        if not v:
            msg = "Debes aceptar los terminos y condiciones"
            raise ValueError(msg)
        return v


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


class RegisterEmpresaSchema(BaseModel):
    """Schema para registro de empresa + usuario gerente"""

    # Datos del Local/Empresa
    rut_empresa: str = Field(..., min_length=9, max_length=12)
    razon_social: str = Field(..., min_length=3)
    nombre_local: str = Field(..., min_length=2, max_length=200)
    telefono_local: str
    correo_local: EmailStr
    descripcion: str | None = None
    id_tipo_local: int = Field(..., ge=1, le=3)  # 1=Restaurante, 2=Bar, 3=Restobar

    # Datos de Direccion
    calle: str = Field(..., min_length=3)
    numero: int = Field(..., gt=0)
    id_comuna: int = Field(..., ge=1)

    # Datos del Usuario Gerente
    nombre_gerente: str = Field(..., min_length=2)
    correo_gerente: EmailStr
    telefono_gerente: str
    contrasena: str = Field(..., min_length=6)

    # Terminos y condiciones B2B
    acepta_terminos: bool = Field(..., description="Acepta terminos y condiciones B2B")

    # pyrefly: ignore  # bad-argument-type
    @field_validator("telefono_local", "telefono_gerente")
    @classmethod
    def validar_telefono(cls, v: str) -> str:
        telefono_limpio = v.replace("+56", "").replace(" ", "").replace("-", "")
        if not telefono_limpio.isdigit() or len(telefono_limpio) != 9:
            msg = "Telefono invalido. Debe tener 9 digitos"
            raise ValueError(msg)
        return telefono_limpio

    # pyrefly: ignore  # bad-argument-type
    @field_validator("acepta_terminos")
    @classmethod
    def validar_terminos(cls, v: bool) -> bool:
        if not v:
            msg = "Debes aceptar los terminos y condiciones"
            raise ValueError(msg)
        return v

    # pyrefly: ignore  # bad-argument-type
    @field_validator("rut_empresa")
    @classmethod
    def validar_formato_rut(cls, v: str) -> str:
        # Limpia el RUT
        rut_limpio = v.replace(".", "").replace(" ", "").upper()
        # Valida formato basico
        import re

        if not re.match(r"^\d{7,8}-[\dK]$", rut_limpio):
            msg = "Formato de RUT invalido. Use formato XX.XXX.XXX-X"
            raise ValueError(msg)
        return rut_limpio
