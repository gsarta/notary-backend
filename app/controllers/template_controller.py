from flask import Blueprint, request, jsonify, g
from app.services.template_service import (
    TemplateService,
)
from app.models.base import get_db
import uuid
import logging

bp = Blueprint("template", __name__, url_prefix="/api/templates")
logger = logging.getLogger(__name__)


# Middleware para inyectar el servicio de Template en el contexto de la solicitud
@bp.before_request
def before_request_templates():
    g.db_session = next(get_db())
    g.template_service = TemplateService(g.db_session)


# Función para cerrar la sesión de la base de datos al finalizar cada solicitud
@bp.teardown_request
def teardown_db_session_templates(exception):
    db_session = g.pop("db_session", None)
    if db_session is not None:
        db_session.close()


@bp.route("/", methods=["GET"])
def get_all_templates():
    """Obtiene todas las plantillas."""
    try:
        templates = g.template_service.get_all_templates()
        return jsonify(templates), 200
    except Exception as e:
        logger.exception("Error al obtener todas las plantillas.")
        return (
            jsonify({"message": "Error interno del servidor al obtener plantillas."}),
            500,
        )


@bp.route("/<uuid:template_id>", methods=["GET"])
def get_template_by_id(template_id: uuid.UUID):
    """Obtiene una plantilla por su ID."""
    try:
        template = g.template_service.get_template_by_id(template_id)
        if template:
            return jsonify(template), 200
        return jsonify({"message": "Plantilla no encontrada"}), 404
    except Exception as e:
        logger.exception(f"Error al obtener plantilla con ID {template_id}.")
        return (
            jsonify({"message": "Error interno del servidor al obtener plantilla."}),
            500,
        )


@bp.route("/", methods=["POST"])
def create_template():
    """Crea una nueva plantilla."""
    data = request.get_json()
    if not data:
        return (
            jsonify({"message": "Se requiere cuerpo de la solicitud en formato JSON."}),
            400,
        )

    try:
        new_template = g.template_service.create_template(data)
        return (
            jsonify(
                {"message": "Plantilla creada exitosamente", "template": new_template}
            ),
            201,
        )
    except ValueError as e:  # Errores de validación de esquema
        return jsonify({"message": str(e)}), 400
    except RuntimeError as e:
        logger.error(f"Error en el servicio al crear plantilla: {e}")
        return jsonify({"message": str(e)}), 409
    except Exception as e:
        logger.exception("Error inesperado al crear plantilla.")
        return (
            jsonify({"message": "Error interno del servidor al crear plantilla."}),
            500,
        )


@bp.route("/<uuid:template_id>", methods=["PATCH"])
def update_template(template_id: uuid.UUID):
    """Actualiza una plantilla existente."""
    data = request.get_json()
    if not data:
        return (
            jsonify({"message": "Se requiere cuerpo de la solicitud en formato JSON."}),
            400,
        )
    if not data:
        return jsonify({"message": "No se proporcionaron datos para actualizar."}), 400

    try:
        updated_template = g.template_service.update_template(template_id, data)
        if updated_template:
            return (
                jsonify(
                    {
                        "message": "Plantilla actualizada exitosamente",
                        "template": updated_template,
                    }
                ),
                200,
            )
        return jsonify({"message": "Plantilla no encontrada"}), 404
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except RuntimeError as e:
        logger.error(f"Error en el servicio al actualizar plantilla {template_id}: {e}")
        return jsonify({"message": str(e)}), 409
    except Exception as e:
        logger.exception(f"Error inesperado al actualizar plantilla {template_id}.")
        return (
            jsonify({"message": "Error interno del servidor al actualizar plantilla."}),
            500,
        )


@bp.route("/<uuid:template_id>", methods=["DELETE"])
def delete_template(template_id: uuid.UUID):
    """Elimina una plantilla."""
    try:
        deleted = g.template_service.delete_template(template_id)
        if deleted:
            return (
                jsonify({"message": "Plantilla eliminada exitosamente"}),
                204,
            )  # No Content
        return jsonify({"message": "Plantilla no encontrada"}), 404
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except RuntimeError as e:
        logger.error(f"Error en el servicio al eliminar plantilla {template_id}: {e}")
        return (
            jsonify({"message": str(e)}),
            409,
        )
    except Exception as e:
        logger.exception(f"Error inesperado al eliminar plantilla {template_id}.")
        return (
            jsonify({"message": "Error interno del servidor al eliminar plantilla."}),
            500,
        )
