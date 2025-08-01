from flask import Blueprint, request, jsonify, g, current_app
from app.services.document_service import DocumentService
from app.schemas.document_schema import (
    DocumentSchema,
    DocumentCreateSchema,
    DocumentUpdateSchema,
)
from app.models.base import get_db
import uuid
import logging
from marshmallow import (
    ValidationError,
)

from app.services.template_service import TemplateService
from app.services.template_section_composition_service import (
    TemplateSectionCompositionService,
)
from app.services.template_section_service import TemplateSectionService

bp = Blueprint("documents", __name__, url_prefix="/api/documents")
document_schema = DocumentSchema()
documents_schema = DocumentSchema(many=True)
document_create_schema = DocumentCreateSchema()
document_update_schema = DocumentUpdateSchema()

logger = logging.getLogger(__name__)


# Middleware para inyectar el servicio de documentos y sus dependencias en el contexto de la solicitud
@bp.before_request
def before_request():
    g.db_session = next(get_db())
    g.template_service = TemplateService(g.db_session)
    g.template_section_service = TemplateSectionService(g.db_session)
    g.template_section_composition_service = TemplateSectionCompositionService(
        g.db_session
    )
    g.document_service = DocumentService(
        g.db_session,
        g.template_service,
        g.template_section_composition_service,
        g.template_section_service,
    )


# Función para cerrar la sesión de la base de datos al finalizar el contexto de la aplicación
@bp.teardown_request
def teardown_db_session(exception):
    db_session = g.pop("db_session", None)
    if db_session is not None:
        db_session.close()


@bp.route("/", methods=["GET"])
def get_documents():
    """Obtiene una lista de todos los documentos."""
    try:
        documents = g.document_service.get_all_documents()
        return jsonify(documents), 200
    except Exception as e:
        logger.exception("Error al obtener documentos.")
        return (
            jsonify({"message": "Error interno del servidor al obtener documentos."}),
            500,
        )


@bp.route("/<uuid:document_id>", methods=["GET"])
def get_document(document_id: uuid.UUID):
    """Obtiene un documento por su ID."""
    try:
        document = g.document_service.get_document_by_id(document_id)
        if document:
            return (
                jsonify(document),
                200,
            )
        return jsonify({"message": "Documento no encontrado."}), 404
    except Exception as e:
        logger.exception(f"Error al obtener documento con ID {document_id}.")
        return (
            jsonify({"message": "Error interno del servidor al obtener documento."}),
            500,
        )


@bp.route("/", methods=["POST"])
def create_document():
    """Crea un nuevo documento."""
    try:
        # Validar la entrada con el esquema de creación
        document_data = document_create_schema.load(request.json)

        new_document = g.document_service.create_document(document_data)
        return (
            jsonify(new_document),
            201,
        )
    except ValidationError as e:
        logger.error(f"Error de validación al crear documento: {e.messages}")
        return jsonify({"message": "Error de validación", "errors": e.messages}), 400
    except ValueError as e:
        logger.error(f"Error de negocio al crear documento: {e}")
        return jsonify({"message": str(e)}), 400
    except RuntimeError as e:
        logger.error(f"Error en el servicio/repositorio al crear documento: {e}")
        return jsonify({"message": str(e)}), 500
    except Exception as e:
        logger.exception("Error interno del servidor al crear documento.")
        return (
            jsonify({"message": f"Error interno del servidor al crear documento: {e}"}),
            500,
        )


@bp.route("/<uuid:document_id>", methods=["PATCH"])
def update_document(document_id: uuid.UUID):
    """Actualiza un documento existente."""
    try:
        update_data = document_update_schema.load(request.json, partial=True)

        updated_document = g.document_service.update_document(document_id, update_data)
        if updated_document:
            return (
                jsonify(updated_document),
                200,
            )
        return jsonify({"message": "Documento no encontrado."}), 404
    except ValidationError as e:
        logger.error(f"Error de validación al actualizar documento: {e.messages}")
        return jsonify({"message": "Error de validación", "errors": e.messages}), 400
    except ValueError as e:
        logger.error(f"Error de negocio al actualizar documento: {e}")
        return jsonify({"message": str(e)}), 400
    except RuntimeError as e:
        logger.error(f"Error en el servicio/repositorio al actualizar documento: {e}")
        return jsonify({"message": str(e)}), 500
    except Exception as e:
        logger.exception(
            f"Error interno del servidor al actualizar documento con ID {document_id}."
        )
        return (
            jsonify(
                {"message": f"Error interno del servidor al actualizar documento: {e}"}
            ),
            500,
        )


@bp.route("/<uuid:document_id>", methods=["DELETE"])
def delete_document(document_id: uuid.UUID):
    """Elimina un documento."""
    try:
        if g.document_service.delete_document(document_id):
            return (
                jsonify({"message": "Documento eliminado exitosamente."}),
                204,
            )
        return jsonify({"message": "Documento no encontrado."}), 404
    except RuntimeError as e:
        logger.error(f"Error en el servicio/repositorio al eliminar documento: {e}")
        return (
            jsonify({"message": str(e)}),
            400,
        )
    except Exception as e:
        logger.exception(
            f"Error interno del servidor al eliminar documento con ID {document_id}."
        )
        return (
            jsonify(
                {"message": f"Error interno del servidor al eliminar documento: {e}"}
            ),
            500,
        )
