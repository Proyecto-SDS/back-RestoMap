# Mapeo de códigos ACTECO chilenos más comunes
# Fuente: Servicio de Impuestos Internos (SII)
# Enfocado en gastronomía, comercio y servicios relacionados

ACTECO_MAPPING = {
    # RESTAURANTES Y SERVICIOS DE COMIDA
    "561011": "Restaurantes",
    "561012": "Fuentes de soda",
    "561013": "Salones de té",
    "561019": "Otros servicios de expendio de comidas preparadas",
    "561020": "Servicio de preparación de comidas para eventos",
    "562110": "Suministro de comidas por encargo",
    "562120": "Concesionarias de casino",
    "562900": "Otros servicios de comidas",
    # BARES Y BEBIDAS
    "563000": "Bares y discotecas",
    "563001": "Bares",
    "563002": "Discotecas",
    "563003": "Pubs",
    "563009": "Otros servicios de expendio de bebidas alcohólicas",
    # COMERCIO AL POR MAYOR - ALIMENTOS
    "463110": "Venta al por mayor de frutas y verduras",
    "463120": "Venta al por mayor de leche y productos lácteos",
    "463130": "Venta al por mayor de productos de confitería",
    "463140": "Venta al por mayor de aceites y grasas comestibles",
    "463150": "Venta al por mayor de bebidas alcohólicas",
    "463160": "Venta al por mayor de bebidas no alcohólicas",
    "463190": "Venta al por mayor de otros productos alimenticios",
    "463910": "Venta al por mayor de productos alimenticios en general",
    # COMERCIO AL POR MENOR - ALIMENTOS
    "471110": "Venta al por menor en supermercados",
    "471120": "Venta al por menor en minimercados",
    "471910": "Venta al por menor en almacenes",
    "472110": "Venta al por menor de frutas y verduras",
    "472120": "Venta al por menor de carnes",
    "472130": "Venta al por menor de pescados y mariscos",
    "472140": "Venta al por menor de productos de panadería",
    "472150": "Venta al por menor de productos lácteos y huevos",
    "472160": "Venta al por menor de confites y productos de confitería",
    "472190": "Venta al por menor de otros productos alimenticios",
    "472300": "Venta al por menor de bebidas",
    # TELECOMUNICACIONES
    "611000": "Telecomunicaciones por cable",
    "612000": "Telecomunicaciones inalámbricas",
    "613000": "Telecomunicaciones por satélite",
    "619000": "Otras actividades de telecomunicaciones",
    "469000": "Venta al por mayor de otros productos",
    # SERVICIOS PROFESIONALES
    "620100": "Programación informática",
    "620200": "Consultoría de informática",
    "631100": "Procesamiento de datos y hospedaje",
    "702000": "Consultoría de gestión",
    "711000": "Servicios de arquitectura e ingeniería",
    "721000": "Investigación y desarrollo",
    "731100": "Publicidad",
    "749000": "Otras actividades profesionales",
    # SERVICIOS DE ALOJAMIENTO
    "551011": "Hoteles",
    "551012": "Hoteles con casino",
    "551019": "Otros servicios de alojamiento para turistas",
    "551020": "Campings y parques para vehículos recreacionales",
    "559000": "Otros tipos de alojamiento",
    # TRANSPORTE Y DELIVERY
    "531020": "Otras actividades de correo",
    "532100": "Servicios de mensajería",
    "493000": "Transporte de carga por vía terrestre",
    # SERVICIOS PERSONALES Y OTROS
    "960900": "Otras actividades de servicios personales",
    "960910": "Servicios de lavandería y tintorería",
    "960920": "Peluquería y otros tratamientos de belleza",
    "960930": "Pompas fúnebres",
    # COMERCIO GENERAL
    "469010": "Venta al por mayor no especializada",
    "471900": "Otros comercios al por menor en establecimientos",
    "479100": "Venta al por menor por correo o internet",
}


def obtener_descripcion_acteco(codigo: str) -> str:
    """
    Obtiene la descripción de un código ACTECO desde el mapeo local.

    Args:
        codigo: Código ACTECO (puede incluir o no puntos)

    Returns:
        Descripción del ACTECO o el código formateado si no se encuentra
    """
    # Limpiar código (quitar puntos, espacios)
    codigo_limpio = str(codigo).replace(".", "").replace(" ", "").strip()

    # Buscar en el diccionario
    descripcion = ACTECO_MAPPING.get(codigo_limpio)

    if descripcion:
        return descripcion
    else:
        # Si no está en el mapeo, retornar código formateado
        return f"Código ACTECO {codigo_limpio}"


def obtener_descripciones_actecos(codigos: list[str]) -> str:
    """
    Convierte una lista de códigos ACTECO en descripciones legibles.

    Args:
        codigos: Lista de códigos ACTECO

    Returns:
        String con descripciones separadas por comas
    """
    if not codigos:
        return ""

    # Limitar a primeros 3 para no hacer muy largo
    codigos_a_mostrar = codigos[:3]
    descripciones = [obtener_descripcion_acteco(cod) for cod in codigos_a_mostrar]

    resultado = ", ".join(descripciones)

    # Agregar indicador si hay más códigos
    if len(codigos) > 3:
        resultado += f" (+{len(codigos) - 3} más)"

    return resultado
