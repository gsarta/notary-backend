from flask import Blueprint, request, jsonify, g
from app.services.user_service import UserService
from app.models.base import get_db
import uuid
import logging

bp = Blueprint("users", __name__, url_prefix="/api/users")
logger = logging.getLogger(__name__)


# Middleware para inyectar el servicio de usuario en el contexto de la solicitud
@bp.before_request
def before_request_users():
    g.db_session = next(get_db())
    g.user_service = UserService(g.db_session)


# Función para cerrar la sesión de la base de datos al finalizar cada solicitud
@bp.teardown_request
def teardown_db_session_users(exception):
    db_session = g.pop("db_session", None)
    if db_session is not None:
        db_session.close()


@bp.route("/", methods=["GET"])
def get_all_users():
    """Obtiene todos los usuarios."""
    try:
        users = g.user_service.get_all_users()
        # Serializar los usuarios a un formato JSON adecuado
        users_data = [
            {
                "user_id": str(user.user_id),
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_active": user.is_active,
                "role_id": str(user.role_id),
                "role_name": (
                    user.role.role_name if user.role else None
                ),  # Asegura que se muestre el nombre del rol
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat(),
            }
            for user in users
        ]
        return jsonify(users_data), 200
    except Exception as e:
        logger.exception("Error al obtener todos los usuarios.")
        return (
            jsonify({"message": "Error interno del servidor al obtener usuarios."}),
            500,
        )


@bp.route("/<uuid:user_id>", methods=["GET"])
def get_user_by_id(user_id: uuid.UUID):
    """Obtiene un usuario por su ID."""
    try:
        user = g.user_service.get_user_by_id(user_id)
        if user:
            return (
                jsonify(
                    {
                        "user_id": str(user.user_id),
                        "username": user.username,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "is_active": user.is_active,
                        "role_id": str(user.role_id),
                        "role_name": user.role.role_name if user.role else None,
                        "created_at": user.created_at.isoformat(),
                        "updated_at": user.updated_at.isoformat(),
                    }
                ),
                200,
            )
        return jsonify({"message": "Usuario no encontrado"}), 404
    except Exception as e:
        logger.exception(f"Error al obtener usuario con ID {user_id}.")
        return (
            jsonify({"message": "Error interno del servidor al obtener usuario."}),
            500,
        )


@bp.route("/", methods=["POST"])
def create_user():
    """Crea un nuevo usuario."""
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    role_id = data.get("role_id")
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    is_active = data.get("is_active", True)

    if not username or not email or not role_id:
        return (
            jsonify(
                {
                    "message": "El nombre de usuario, correo electrónico y ID de rol son obligatorios."
                }
            ),
            400,
        )

    try:
        # Asegurarse de que role_id es un UUID válido
        role_id_uuid = uuid.UUID(role_id)
    except ValueError:
        return (
            jsonify({"message": "El ID de rol proporcionado no es un UUID válido."}),
            400,
        )

    try:
        new_user = g.user_service.create_user(
            username, email, role_id_uuid, first_name, last_name, is_active
        )
        return (
            jsonify(
                {
                    "message": "Usuario creado exitosamente",
                    "user_id": str(new_user.user_id),
                    "username": new_user.username,
                    "email": new_user.email,
                }
            ),
            201,
        )
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except RuntimeError as e:
        logger.error(f"Error en el servicio al crear usuario: {e}")
        return jsonify({"message": str(e)}), 500
    except Exception as e:
        logger.exception("Error inesperado al crear usuario.")
        return jsonify({"message": "Error interno del servidor al crear usuario."}), 500


@bp.route("/<uuid:user_id>", methods=["PATCH"])
def update_user(user_id: uuid.UUID):
    """Actualiza un usuario existente."""
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    role_id = data.get("role_id")
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    is_active = data.get("is_active")

    # Asegurarse de que al menos un campo se esté intentando actualizar
    if not any(
        [username, email, role_id, first_name, last_name, is_active is not None]
    ):
        return jsonify({"message": "No se proporcionaron datos para actualizar."}), 400

    # Validar role_id si se proporciona
    if role_id is not None:
        try:
            role_id_uuid = uuid.UUID(role_id)
        except ValueError:
            return (
                jsonify(
                    {"message": "El ID de rol proporcionado no es un UUID válido."}
                ),
                400,
            )
    else:
        role_id_uuid = None

    try:
        updated_user = g.user_service.update_user(
            user_id, username, email, role_id_uuid, first_name, last_name, is_active
        )
        return (
            jsonify(
                {
                    "message": "Usuario actualizado exitosamente",
                    "user_id": str(updated_user.user_id),
                    "username": updated_user.username,
                    "email": updated_user.email,
                }
            ),
            200,
        )
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except RuntimeError as e:
        logger.error(f"Error en el servicio al actualizar usuario {user_id}: {e}")
        return jsonify({"message": str(e)}), 500
    except Exception as e:
        logger.exception(f"Error inesperado al actualizar usuario {user_id}.")
        return (
            jsonify({"message": "Error interno del servidor al actualizar usuario."}),
            500,
        )


@bp.route("/<uuid:user_id>", methods=["DELETE"])
def delete_user(user_id: uuid.UUID):
    """Elimina un usuario."""
    try:
        deleted = g.user_service.delete_user(user_id)
        if deleted:
            return jsonify({"message": "Usuario eliminado exitosamente"}), 204
        return jsonify({"message": "Usuario no encontrado o no se pudo eliminar"}), 404
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except RuntimeError as e:
        logger.error(f"Error en el servicio al eliminar usuario {user_id}: {e}")
        return jsonify({"message": str(e)}), 500
    except Exception as e:
        logger.exception(f"Error inesperado al eliminar usuario {user_id}.")
        return (
            jsonify({"message": "Error interno del servidor al eliminar usuario."}),
            500,
        )
