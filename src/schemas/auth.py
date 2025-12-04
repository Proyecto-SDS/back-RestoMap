"""
Schemas para autenticación y usuarios.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr


class UsuarioBase(BaseModel):
    """Schema base de usuario"""

    nombre: str
    correo: EmailStr
    telefono: str | None = None


class UsuarioCreateSchema(UsuarioBase):
    """Schema para crear usuario"""

    contrasena: str
    id_rol: int = 2  # Por defecto: usuario normal


class UsuarioUpdateSchema(BaseModel):
    """Schema para actualizar usuario"""

    nombre: str | None = None
    telefono: str | None = None
    correo: EmailStr | None = None


class UsuarioResponseSchema(UsuarioBase):
    """Schema de respuesta de usuario (sin contraseña)"""

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
    contrasena: str


class RegisterSchema(UsuarioCreateSchema):
    """Schema para registro (alias de UsuarioCreateSchema)"""

    pass


class RolSchema(BaseModel):
    """Schema de rol"""

    id: int | None = None
    nombre: str

    class Config:
        from_attributes = True
