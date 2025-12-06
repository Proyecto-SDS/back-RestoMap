"""
Servicio de validacion de RUT chileno.
Incluye validacion de formato y consulta a API SimpleAPI.cl
"""

import os
import re

import requests

from config import get_logger

logger = get_logger(__name__)

# Configuracion API SimpleAPI.cl v2
SIMPLEAPI_URL = "https://rut.simpleapi.cl/v2"
SIMPLEAPI_KEY = os.getenv("SIMPLEAPI_KEY", "")


def limpiar_rut(rut: str) -> str:
    """
    Limpia el RUT removiendo puntos y espacios.
    Retorna formato XXXXXXXX-X
    """
    rut_limpio = rut.replace(".", "").replace(" ", "").upper()
    return rut_limpio


def validar_formato_rut(rut: str) -> bool:
    """
    Valida el formato del RUT chileno.
    Acepta formatos: XX.XXX.XXX-X, XXXXXXXX-X
    """
    rut_limpio = limpiar_rut(rut)

    # Patron: 7-8 digitos, guion, digito verificador (0-9 o K)
    patron = r"^\d{7,8}-[\dK]$"
    return bool(re.match(patron, rut_limpio))


def calcular_digito_verificador(rut_sin_dv: str) -> str:
    """
    Calcula el digito verificador de un RUT usando modulo 11.
    """
    # Limpiar y obtener solo numeros
    rut_numeros = rut_sin_dv.replace(".", "").replace("-", "").replace(" ", "")

    # Algoritmo modulo 11
    suma = 0
    multiplicador = 2

    for digito in reversed(rut_numeros):
        suma += int(digito) * multiplicador
        multiplicador = multiplicador + 1 if multiplicador < 7 else 2

    resto = suma % 11
    dv = 11 - resto

    if dv == 11:
        return "0"
    elif dv == 10:
        return "K"
    else:
        return str(dv)


def validar_digito_verificador(rut: str) -> bool:
    """
    Verifica que el digito verificador del RUT sea correcto.
    """
    rut_limpio = limpiar_rut(rut)

    if "-" not in rut_limpio:
        return False

    partes = rut_limpio.split("-")
    if len(partes) != 2:
        return False

    rut_numeros = partes[0]
    dv_ingresado = partes[1].upper()

    dv_calculado = calcular_digito_verificador(rut_numeros)

    return dv_ingresado == dv_calculado


def consultar_rut_sii(rut: str) -> dict:
    """
    Consulta la API SimpleAPI.cl v2 para obtener informacion de un contribuyente.

    Args:
        rut: RUT del contribuyente (con o sin puntos)

    Returns:
        dict con:
            - valido: bool - Si la consulta fue exitosa
            - existe: bool - Si el RUT existe en el SII
            - razon_social: str | None
            - glosa_giro: str | None
            - error: str | None - Mensaje de error si aplica
    """
    rut_limpio = limpiar_rut(rut)

    # Validar formato y digito verificador primero
    if not validar_formato_rut(rut):
        return {
            "valido": False,
            "existe": False,
            "razon_social": None,
            "glosa_giro": None,
            "error": "Formato de RUT invalido",
        }

    if not validar_digito_verificador(rut):
        return {
            "valido": False,
            "existe": False,
            "razon_social": None,
            "glosa_giro": None,
            "error": "Digito verificador incorrecto",
        }

    # Si no hay API Key configurada, solo validar formato localmente
    if not SIMPLEAPI_KEY:
        logger.warning("SIMPLEAPI_KEY no configurada, validando solo formato")
        return {
            "valido": True,
            "existe": True,  # Asumimos que existe si pasa validacion local
            "razon_social": None,
            "glosa_giro": None,
            "error": None,
        }

    try:
        # Consultar API SimpleAPI.cl v2
        headers = {
            "Authorization": SIMPLEAPI_KEY,
        }

        # GET request con RUT en el path (API v2)
        response = requests.get(
            f"{SIMPLEAPI_URL}/{rut_limpio}",
            headers=headers,
            timeout=20,  # La API puede tardar entre 5-15 segundos
        )

        # Manejar errores HTTP especificos
        if response.status_code == 400:
            error_msg = (
                response.text if response.text else "RUT invalido o no existe en el SII"
            )
            return {
                "valido": True,
                "existe": False,
                "razon_social": None,
                "glosa_giro": None,
                "error": error_msg,
            }

        if response.status_code == 401:
            logger.error("API Key invalida o sin suscripcion habilitada")
            return {
                "valido": False,
                "existe": False,
                "razon_social": None,
                "glosa_giro": None,
                "error": "Error de autenticacion con el servicio de validacion",
            }

        response.raise_for_status()

        data = response.json()

        # Verificar respuesta de SimpleAPI v2
        if not data or "razonSocial" not in data:
            return {
                "valido": True,
                "existe": False,
                "razon_social": None,
                "glosa_giro": None,
                "error": "RUT no encontrado en el SII",
            }

        # Extraer primera actividad economica si existe
        giro = None
        actividades = data.get("actividadesEconomicas", [])
        if actividades and len(actividades) > 0:
            giro = actividades[0].get("descripcion")

        return {
            "valido": True,
            "existe": True,
            "razon_social": data.get("razonSocial"),
            "glosa_giro": giro,
            "error": None,
        }

    except requests.exceptions.Timeout:
        logger.error("Timeout al consultar API SimpleAPI.cl")
        return {
            "valido": False,
            "existe": False,
            "razon_social": None,
            "glosa_giro": None,
            "error": "Tiempo de espera agotado al consultar el SII",
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Error al consultar API SimpleAPI.cl: {e}")
        return {
            "valido": False,
            "existe": False,
            "razon_social": None,
            "glosa_giro": None,
            "error": "Error al conectar con el servicio de validacion",
        }
    except Exception as e:
        logger.error(f"Error inesperado en consulta RUT: {e}")
        return {
            "valido": False,
            "existe": False,
            "razon_social": None,
            "glosa_giro": None,
            "error": "Error inesperado al validar el RUT",
        }
