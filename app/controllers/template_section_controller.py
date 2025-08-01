from flask import Blueprint, request, jsonify, g
from app.services.template_section_service import TemplateSectionService
from app.models.base import get_db
import uuid
import logging

bp = Blueprint("template_sections", __name__, url_prefix="/api/template-sections")
logger = logging.getLogger(__name__)


# Middleware para inyectar el servicio de TemplateSection en el contexto de la solicitud
@bp.before_request
def before_request_template_sections():
    g.db_session = next(get_db())
    g.template_section_service = TemplateSectionService(g.db_session)


# Función para cerrar la sesión de la base de datos al finalizar cada solicitud
@bp.teardown_request
def teardown_db_session_template_sections(exception):
    db_session = g.pop("db_session", None)
    if db_session is not None:
        db_session.close()


@bp.route("/", methods=["GET"])
def get_all_template_sections():
    """Obtiene todas las secciones de plantilla."""
    try:
        sections = g.template_section_service.get_all_template_sections()
        return jsonify(sections), 200
    except Exception as e:
        logger.exception("Error al obtener todas las secciones de plantilla.")
        return (
            jsonify(
                {
                    "message": "Error interno del servidor al obtener secciones de plantilla."
                }
            ),
            500,
        )


@bp.route("/<uuid:section_id>", methods=["GET"])
def get_template_section_by_id(section_id: uuid.UUID):
    """Obtiene una sección de plantilla por su ID."""
    try:
        section = g.template_section_service.get_template_section_by_id(section_id)
        if section:
            return jsonify(section), 200
        return jsonify({"message": "Sección de plantilla no encontrada"}), 404
    except Exception as e:
        logger.exception(f"Error al obtener sección de plantilla con ID {section_id}.")
        return (
            jsonify(
                {
                    "message": "Error interno del servidor al obtener sección de plantilla."
                }
            ),
            500,
        )


@bp.route("/", methods=["POST"])
def create_template_section():
    """Crea una nueva sección de plantilla."""
    data = request.get_json()
    if not data:
        return (
            jsonify({"message": "Se requiere cuerpo de la solicitud en formato JSON."}),
            400,
        )

    try:
        new_section = g.template_section_service.create_template_section(data)
        return (
            jsonify(
                {
                    "message": "Sección de plantilla creada exitosamente",
                    "section": new_section,
                }
            ),
            201,
        )
    except ValueError as e:  # Errores de validación de esquema desde el servicio
        return jsonify({"message": str(e)}), 400
    except (
        RuntimeError
    ) as e:  # Errores de lógica de negocio desde el servicio/repositorio
        logger.error(f"Error en el servicio al crear sección de plantilla: {e}")
        return jsonify({"message": str(e)}), 409
    except Exception as e:
        logger.exception("Error inesperado al crear sección de plantilla.")
        return (
            jsonify(
                {"message": "Error interno del servidor al crear sección de plantilla."}
            ),
            500,
        )


@bp.route("/<uuid:section_id>", methods=["PATCH"])
def update_template_section(section_id: uuid.UUID):
    """Actualiza una sección de plantilla existente."""
    data = request.get_json()
    if not data:
        return (
            jsonify({"message": "Se requiere cuerpo de la solicitud en formato JSON."}),
            400,
        )
    if not data:
        return jsonify({"message": "No se proporcionaron datos para actualizar."}), 400

    try:
        updated_section = g.template_section_service.update_template_section(
            section_id, data
        )
        if updated_section:
            return (
                jsonify(
                    {
                        "message": "Sección de plantilla actualizada exitosamente",
                        "section": updated_section,
                    }
                ),
                200,
            )
        return jsonify({"message": "Sección de plantilla no encontrada"}), 404
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except RuntimeError as e:
        logger.error(
            f"Error en el servicio al actualizar sección de plantilla {section_id}: {e}"
        )
        return jsonify({"message": str(e)}), 409
    except Exception as e:
        logger.exception(
            f"Error inesperado al actualizar sección de plantilla {section_id}."
        )
        return (
            jsonify(
                {
                    "message": "Error interno del servidor al actualizar sección de plantilla."
                }
            ),
            500,
        )


@bp.route("/<uuid:section_id>", methods=["DELETE"])
def delete_template_section(section_id: uuid.UUID):
    """Elimina una sección de plantilla."""
    try:
        deleted = g.template_section_service.delete_template_section(section_id)
        if deleted:
            return (
                jsonify({"message": "Sección de plantilla eliminada exitosamente"}),
                204,
            )  # No Content
        return jsonify({"message": "Sección de plantilla no encontrada"}), 404
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except RuntimeError as e:  # Error por FK constraint, si la sección está en uso
        logger.error(
            f"Error en el servicio al eliminar sección de plantilla {section_id}: {e}"
        )
        return jsonify({"message": str(e)}), 409
    except Exception as e:
        logger.exception(
            f"Error inesperado al eliminar sección de plantilla {section_id}."
        )
        return (
            jsonify(
                {
                    "message": "Error interno del servidor al eliminar sección de plantilla."
                }
            ),
            500,
        )
