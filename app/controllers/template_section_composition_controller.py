from flask import Blueprint, request, jsonify, g
from app.services.template_section_composition_service import (
    TemplateSectionCompositionService,
)
from app.models.base import get_db
import uuid
import logging

bp = Blueprint(
    "template_section_compositions",
    __name__,
    url_prefix="/api/template-section-compositions",
)
logger = logging.getLogger(__name__)


# Middleware para inyectar el servicio de TemplateSectionComposition en el contexto de la solicitud
@bp.before_request
def before_request_template_section_compositions():
    g.db_session = next(get_db())
    g.template_section_composition_service = TemplateSectionCompositionService(
        g.db_session
    )


# Función para cerrar la sesión de la base de datos al finalizar cada solicitud
@bp.teardown_request
def teardown_db_session_template_section_compositions(exception):
    db_session = g.pop("db_session", None)
    if db_session is not None:
        db_session.close()


@bp.route("/", methods=["GET"])
def get_all_template_section_compositions():
    """Obtiene todas las composiciones de secciones de plantilla."""
    try:
        compositions = g.template_section_composition_service.get_all_compositions()
        return jsonify(compositions), 200
    except Exception as e:
        logger.exception(
            "Error al obtener todas las composiciones de secciones de plantilla."
        )
        return (
            jsonify(
                {"message": "Error interno del servidor al obtener composiciones."}
            ),
            500,
        )


@bp.route("/<uuid:template_id>/sections/<uuid:section_id>", methods=["GET"])
def get_template_section_composition_by_ids(
    template_id: uuid.UUID, section_id: uuid.UUID
):
    """Obtiene una composición de sección por su ID de plantilla y ID de sección (PK compuesto)."""
    try:
        composition = g.template_section_composition_service.get_composition_by_ids(
            template_id, section_id
        )
        if composition:
            return jsonify(composition), 200
        return jsonify({"message": "Composición de sección no encontrada"}), 404
    except Exception as e:
        logger.exception(
            f"Error al obtener composición con template_id {template_id} y section_id {section_id}."
        )
        return (
            jsonify({"message": "Error interno del servidor al obtener composición."}),
            500,
        )


@bp.route("/by-template/<uuid:template_id>", methods=["GET"])
def get_template_compositions_by_template_id(template_id: uuid.UUID):
    """Obtiene todas las composiciones para una plantilla específica, ordenadas por order_index."""
    try:
        compositions = (
            g.template_section_composition_service.get_compositions_by_template_id(
                template_id
            )
        )
        if compositions:
            return jsonify(compositions), 200
        return (
            jsonify({"message": "No se encontraron composiciones para esta plantilla"}),
            404,
        )
    except Exception as e:
        logger.exception(
            f"Error al obtener composiciones para template_id {template_id}."
        )
        return (
            jsonify(
                {"message": "Error interno del servidor al obtener composiciones."}
            ),
            500,
        )


@bp.route("/", methods=["POST"])
def create_template_section_composition():
    """Crea una nueva composición de sección de plantilla."""
    data = request.get_json()
    if not data:
        return (
            jsonify({"message": "Se requiere cuerpo de la solicitud en formato JSON."}),
            400,
        )

    try:
        new_composition = g.template_section_composition_service.create_composition(
            data
        )
        return (
            jsonify(
                {
                    "message": "Composición de sección creada exitosamente",
                    "composition": new_composition,
                }
            ),
            201,
        )
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except (
        RuntimeError
    ) as e:  # Errores de lógica de negocio (ej. duplicados de PK o order_index)
        logger.error(f"Error en el servicio al crear composición de sección: {e}")
        return jsonify({"message": str(e)}), 409
    except Exception as e:
        logger.exception("Error inesperado al crear composición de sección.")
        return (
            jsonify(
                {
                    "message": "Error interno del servidor al crear composición de sección."
                }
            ),
            500,
        )


@bp.route("/<uuid:template_id>/sections/<uuid:section_id>", methods=["PATCH"])
def update_template_section_composition(template_id: uuid.UUID, section_id: uuid.UUID):
    """Actualiza una composición de sección de plantilla existente."""
    data = request.get_json()
    if not data:
        return (
            jsonify({"message": "Se requiere cuerpo de la solicitud en formato JSON."}),
            400,
        )
    if not data:
        return jsonify({"message": "No se proporcionaron datos para actualizar."}), 400

    try:
        updated_composition = g.template_section_composition_service.update_composition(
            template_id, section_id, data
        )
        if updated_composition:
            return (
                jsonify(
                    {
                        "message": "Composición de sección actualizada exitosamente",
                        "composition": updated_composition,
                    }
                ),
                200,
            )
        return jsonify({"message": "Composición de sección no encontrada"}), 404
    except ValueError as e:  # Errores de validación de esquema
        return jsonify({"message": str(e)}), 400
    except (
        RuntimeError
    ) as e:  # Errores de lógica de negocio (ej. order_index duplicado)
        logger.error(
            f"Error en el servicio al actualizar composición {template_id}/{section_id}: {e}"
        )
        return jsonify({"message": str(e)}), 409
    except Exception as e:
        logger.exception(
            f"Error inesperado al actualizar composición {template_id}/{section_id}."
        )
        return (
            jsonify(
                {"message": "Error interno del servidor al actualizar composición."}
            ),
            500,
        )


@bp.route("/<uuid:template_id>/sections/<uuid:section_id>", methods=["DELETE"])
def delete_template_section_composition(template_id: uuid.UUID, section_id: uuid.UUID):
    """Elimina una composición de sección de plantilla."""
    try:
        deleted = g.template_section_composition_service.delete_composition(
            template_id, section_id
        )
        if deleted:
            return (
                jsonify({"message": "Composición de sección eliminada exitosamente"}),
                204,
            )
        return jsonify({"message": "Composición de sección no encontrada"}), 404
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except RuntimeError as e:
        logger.error(
            f"Error en el servicio al eliminar composición {template_id}/{section_id}: {e}"
        )
        return jsonify({"message": str(e)}), 500
    except Exception as e:
        logger.exception(
            f"Error inesperado al eliminar composición {template_id}/{section_id}."
        )
        return (
            jsonify({"message": "Error interno del servidor al eliminar composición."}),
            500,
        )
