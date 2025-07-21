from flask import Blueprint, request, jsonify, g
from app.services.role_service import RoleService
from app.models.base import get_db
import uuid
import logging

bp = Blueprint("roles", __name__, url_prefix="/api/roles")
logger = logging.getLogger(__name__)


# Middleware para inyectar el servicio de rol en el contexto de la solicitud
@bp.before_request
def before_request_roles():
    g.db_session = next(get_db())
    g.role_service = RoleService(g.db_session)


# Función para cerrar la sesión de la base de datos al finalizar cada solicitud
@bp.teardown_request
def teardown_db_session_roles(exception):
    db_session = g.pop("db_session", None)
    if db_session is not None:
        db_session.close()


@bp.route("/", methods=["GET"])
def get_all_roles():
    """Obtiene todos los roles."""
    try:
        roles = g.role_service.get_all_roles()
        # Serializar los roles a un formato JSON adecuado
        roles_data = [
            {
                "role_id": str(role.role_id),
                "role_name": role.role_name,
                "description": role.description,
                "created_at": role.created_at.isoformat(),
                "updated_at": role.updated_at.isoformat(),
            }
            for role in roles
        ]
        return jsonify(roles_data), 200
    except Exception as e:
        logger.exception("Error al obtener todos los roles.")
        return jsonify({"message": "Error interno del servidor al obtener roles."}), 500


@bp.route("/<uuid:role_id>", methods=["GET"])
def get_role_by_id(role_id: uuid.UUID):
    """Obtiene un rol por su ID."""
    try:
        role = g.role_service.get_role_by_id(role_id)
        if role:
            return (
                jsonify(
                    {
                        "role_id": str(role.role_id),
                        "role_name": role.role_name,
                        "description": role.description,
                        "created_at": role.created_at.isoformat(),
                        "updated_at": role.updated_at.isoformat(),
                    }
                ),
                200,
            )
        return jsonify({"message": "Rol no encontrado"}), 404
    except Exception as e:
        logger.exception(f"Error al obtener rol con ID {role_id}.")
        return jsonify({"message": "Error interno del servidor al obtener rol."}), 500


@bp.route("/", methods=["POST"])
def create_role():
    """Crea un nuevo rol."""
    data = request.get_json()
    role_name = data.get("role_name")
    description = data.get("description")

    if not role_name:
        return jsonify({"message": "El nombre del rol es obligatorio."}), 400

    try:
        new_role = g.role_service.create_role(role_name, description)
        return (
            jsonify(
                {
                    "message": "Rol creado exitosamente",
                    "role_id": str(new_role.role_id),
                    "role_name": new_role.role_name,
                }
            ),
            201,
        )
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except RuntimeError as e:
        logger.error(f"Error en el servicio al crear rol: {e}")
        return jsonify({"message": str(e)}), 500
    except Exception as e:
        logger.exception("Error inesperado al crear rol.")
        return jsonify({"message": "Error interno del servidor al crear rol."}), 500


@bp.route("/<uuid:role_id>", methods=["PATCH"])
def update_role(role_id: uuid.UUID):
    """Actualiza un rol existente."""
    data = request.get_json()
    role_name = data.get("role_name")
    description = data.get("description")

    # Asegurarse de que al menos un campo se esté intentando actualizar
    if not role_name and not description:
        return jsonify({"message": "No se proporcionaron datos para actualizar."}), 400

    try:
        updated_role = g.role_service.update_role(role_id, role_name, description)
        return (
            jsonify(
                {
                    "message": "Rol actualizado exitosamente",
                    "role_id": str(updated_role.role_id),
                    "role_name": updated_role.role_name,
                }
            ),
            200,
        )
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except RuntimeError as e:
        logger.error(f"Error en el servicio al actualizar rol {role_id}: {e}")
        return jsonify({"message": str(e)}), 500
    except Exception as e:
        logger.exception(f"Error inesperado al actualizar rol {role_id}.")
        return (
            jsonify({"message": "Error interno del servidor al actualizar rol."}),
            500,
        )


@bp.route("/<uuid:role_id>", methods=["DELETE"])
def delete_role(role_id: uuid.UUID):
    """Elimina un rol."""
    try:
        deleted = g.role_service.delete_role(role_id)
        if deleted:
            return jsonify({"message": "Rol eliminado exitosamente"}), 204
        # Si no se elimina pero no hubo error, significa que no se encontró
        return jsonify({"message": "Rol no encontrado o no se pudo eliminar"}), 404
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except RuntimeError as e:
        logger.error(f"Error en el servicio al eliminar rol {role_id}: {e}")
        return jsonify({"message": str(e)}), 500
    except Exception as e:
        logger.exception(f"Error inesperado al eliminar rol {role_id}.")
        return jsonify({"message": "Error interno del servidor al eliminar rol."}), 500
