from flask import Blueprint, request, jsonify
from app.services.document_type_service import DocumentTypeService
from app.models.base import get_db
import logging

# Configuración del logger para este módulo
logger = logging.getLogger(__name__)

# Crear un Blueprint para agrupar las rutas de tipos de documentos
bp = Blueprint("document_types", __name__, url_prefix="/api/document_types")


@bp.route("/", methods=["GET"])
def get_all_document_types():
    """
    Endpoint para obtener todos los tipos de documentos.
    Retorna una lista de tipos de documentos.
    """
    db_session = next(get_db())  # Obtiene una sesión de base de datos
    try:
        service = DocumentTypeService(db_session)
        document_types = service.get_all_document_types()
        return jsonify(document_types), 200
    except Exception as e:
        logger.error(f"Error al obtener todos los tipos de documentos: {e}")
        return (
            jsonify(
                {"message": "Error interno del servidor al obtener tipos de documentos"}
            ),
            500,
        )
    finally:
        db_session.close()


@bp.route("/<string:document_type_id>", methods=["GET"])
def get_document_type_by_id(document_type_id):
    """
    Endpoint para obtener un tipo de documento por su ID.
    Retorna el tipo de documento especificado o un error 404 si no se encuentra.
    """
    db_session = next(get_db())
    try:
        service = DocumentTypeService(db_session)
        document_type = service.get_document_type_by_id(document_type_id)
        return jsonify(document_type), 200
    except ValueError as e:  # Captura errores de validación de ID o no encontrado
        logger.warning(
            f"Error al obtener tipo de documento por ID '{document_type_id}': {e}"
        )
        return jsonify({"message": str(e)}), 404  # Not Found
    except Exception as e:
        logger.error(
            f"Error interno al obtener tipo de documento por ID '{document_type_id}': {e}"
        )
        return (
            jsonify(
                {"message": "Error interno del servidor al obtener tipo de documento"}
            ),
            500,
        )
    finally:
        db_session.close()


@bp.route("/", methods=["POST"])
def create_document_type():
    """
    Endpoint para crear un nuevo tipo de documento.
    Requiere un JSON con 'type_name' (obligatorio) y 'description' (opcional).
    Retorna el tipo de documento creado o un error 400/500.
    """
    db_session = next(get_db())
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "Se requiere cuerpo de solicitud JSON"}), 400

        service = DocumentTypeService(db_session)
        new_document_type = service.create_document_type(data)
        return jsonify(new_document_type), 201  # Created
    except ValueError as e:  # Captura errores de validación o duplicidad de nombre
        logger.warning(
            f"Error de validación o duplicidad al crear tipo de documento: {e}"
        )
        return jsonify({"message": str(e)}), 400  # Bad Request
    except RuntimeError as e:  # Captura errores internos del servicio/repositorio
        logger.error(f"Error en el servicio al crear tipo de documento: {e}")
        return (
            jsonify({"message": "Error en el servicio al crear tipo de documento"}),
            500,
        )
    except Exception as e:
        logger.error(f"Error inesperado al crear tipo de documento: {e}")
        return (
            jsonify(
                {"message": "Error interno del servidor al crear tipo de documento"}
            ),
            500,
        )
    finally:
        db_session.close()


@bp.route("/<string:document_type_id>", methods=["PUT"])
def update_document_type(document_type_id):
    """
    Endpoint para actualizar un tipo de documento existente por su ID.
    Requiere un JSON con los campos a actualizar (type_name, description).
    Retorna el tipo de documento actualizado o un error 400/404/500.
    """
    db_session = next(get_db())
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "Se requiere cuerpo de solicitud JSON"}), 400

        service = DocumentTypeService(db_session)
        updated_document_type = service.update_document_type(document_type_id, data)
        return jsonify(updated_document_type), 200
    except (
        ValueError
    ) as e:  # Captura errores de validación, ID inválido, no encontrado o duplicidad
        logger.warning(
            f"Error al actualizar tipo de documento por ID '{document_type_id}': {e}"
        )
        # Diferenciamos 400 para errores de entrada/duplicidad y 404 para no encontrado
        status_code = (
            400
            if "Datos de entrada inválidos" in str(e) or "Ya existe" in str(e)
            else 404
        )
        return jsonify({"message": str(e)}), status_code
    except RuntimeError as e:  # Captura errores internos del servicio/repositorio
        logger.error(
            f"Error en el servicio al actualizar tipo de documento (ID: {document_type_id}): {e}"
        )
        return (
            jsonify(
                {"message": "Error en el servicio al actualizar tipo de documento"}
            ),
            500,
        )
    except Exception as e:
        logger.error(
            f"Error inesperado al actualizar tipo de documento (ID: {document_type_id}): {e}"
        )
        return (
            jsonify(
                {
                    "message": "Error interno del servidor al actualizar tipo de documento"
                }
            ),
            500,
        )
    finally:
        db_session.close()


@bp.route("/<string:document_type_id>", methods=["DELETE"])
def delete_document_type(document_type_id):
    """
    Endpoint para eliminar un tipo de documento por su ID.
    Retorna un mensaje de éxito sin contenido (204) o un error 404/500.
    """
    db_session = next(get_db())
    try:
        service = DocumentTypeService(db_session)
        service.delete_document_type(document_type_id)
        return (
            jsonify({"message": "Tipo de documento eliminado exitosamente"}),
            204,
        )  # No Content
    except ValueError as e:  # Captura errores de validación de ID o no encontrado
        logger.warning(
            f"Error al eliminar tipo de documento por ID '{document_type_id}': {e}"
        )
        return jsonify({"message": str(e)}), 404  # Not Found
    except RuntimeError as e:  # Captura errores internos del servicio/repositorio
        logger.error(
            f"Error en el servicio al eliminar tipo de documento (ID: {document_type_id}): {e}"
        )
        return (
            jsonify({"message": "Error en el servicio al eliminar tipo de documento"}),
            500,
        )
    except Exception as e:
        logger.error(
            f"Error inesperado al eliminar tipo de documento (ID: {document_type_id}): {e}"
        )
        return (
            jsonify(
                {"message": "Error interno del servidor al eliminar tipo de documento"}
            ),
            500,
        )
    finally:
        db_session.close()
