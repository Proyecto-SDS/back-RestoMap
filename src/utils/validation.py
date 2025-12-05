"""
Helper para validacion de schemas con Pydantic en Flask.
"""

from functools import wraps

from flask import jsonify, request
from pydantic import ValidationError


def validate_json(schema_class):
    """
    Decorador para validar el body JSON de una request con un schema Pydantic.

    Uso:
        @app.route("/login", methods=["POST"])
        @validate_json(LoginSchema)
        def login(data):  # data ya es la instancia validada del schema
            correo = data.correo
            contrasena = data.contrasena
            ...

    Args:
        schema_class: Clase Pydantic para validar

    Returns:
        El decorador que inyecta `data` como primer argumento
    """

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            json_data = request.get_json()

            if json_data is None:
                return jsonify({"error": "Se requiere body JSON"}), 400

            try:
                validated_data = schema_class(**json_data)
            except ValidationError as e:
                # Formatear errores de Pydantic de forma legible
                errors = []
                for error in e.errors():
                    field = ".".join(str(loc) for loc in error["loc"])
                    msg = error["msg"]
                    errors.append(f"{field}: {msg}")

                return jsonify({"error": "Datos invalidos", "details": errors}), 400

            # Inyectar data validada como primer argumento
            return f(validated_data, *args, **kwargs)

        return wrapper

    return decorator


def validate_query_params(schema_class):
    """
    Decorador para validar query params con un schema Pydantic.

    Uso:
        @app.route("/items", methods=["GET"])
        @validate_query_params(PaginationParams)
        def get_items(params):
            page = params.page
            per_page = params.per_page
            ...
    """

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                # Convertir query params a dict
                query_dict = request.args.to_dict()
                validated_params = schema_class(**query_dict)
            except ValidationError as e:
                errors = []
                for error in e.errors():
                    field = ".".join(str(loc) for loc in error["loc"])
                    msg = error["msg"]
                    errors.append(f"{field}: {msg}")

                return jsonify(
                    {"error": "Parametros invalidos", "details": errors}
                ), 400

            return f(validated_params, *args, **kwargs)

        return wrapper

    return decorator
