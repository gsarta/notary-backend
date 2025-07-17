from flask import Blueprint, request, jsonify, current_app, g
from app.schemas.transcription_schema import TranscriptionSchema
from app.services.transcribe_service import TranscribeService
from app.utils.audio_processor import AudioProcessor
from app.utils.azure_blob_manager import AzureBlobManager
from app.models.base import get_db
import uuid
import logging

bp = Blueprint("transcriptions", __name__, url_prefix="/api")
transcription_schema = TranscriptionSchema()
transcriptions_schema = TranscriptionSchema(many=True)

logger = logging.getLogger(__name__)


# Middleware para inyectar el servicio en el contexto de la solicitud
@bp.before_request
def before_request_transcribe():
    g.db_session = next(get_db())
    # Obtener las configuraciones necesarias de current_app.config
    openai_api_key = current_app.config.get("OPENAI_API_KEY")
    azure_storage_account_name = current_app.config.get("AZURE_STORAGE_ACCOUNT_NAME")
    azure_storage_account_key = current_app.config.get("AZURE_STORAGE_ACCOUNT_KEY")
    azure_storage_container_name = current_app.config.get(
        "AZURE_STORAGE_CONTAINER_NAME"
    )

    # Validar que las configuraciones existan
    if not openai_api_key:
        logger.error("OPENAI_API_KEY no configurada.")
        raise RuntimeError("OPENAI_API_KEY no está configurada en la aplicación.")
    if not all(
        [
            azure_storage_account_name,
            azure_storage_account_key,
            azure_storage_container_name,
        ]
    ):
        logger.error("Credenciales de Azure Blob Storage incompletas.")
        raise RuntimeError(
            "Las credenciales de Azure Blob Storage no están configuradas completamente."
        )

    g.audio_processor = AudioProcessor(openai_api_key=openai_api_key)
    g.azure_blob_manager = AzureBlobManager(
        account_name=azure_storage_account_name,
        account_key=azure_storage_account_key,
        container_name=azure_storage_container_name,
    )

    segment_duration_ms_config = current_app.config.get("SEGMENT_DURATION_MS", 300000)
    g.transcribe_service = TranscribeService(
        db_session=g.db_session,
        audio_processor=g.audio_processor,
        azure_blob_manager=g.azure_blob_manager,
        segment_duration_ms=segment_duration_ms_config,
    )


# Función para cerrar la sesión de la base de datos al finalizar cada solicitud
@bp.teardown_request
def teardown_db_session_transcribe(exception):
    db_session = g.pop("db_session", None)
    if db_session is not None:
        db_session.close()


@bp.route("/transcribe", methods=["POST"])
def transcribe_audio():
    """
    Endpoint para recibir un archivo de audio y procesar su transcripción.
    Un usuario enviará un archivo de audio aquí para obtener una transcripción.
    """
    if "audio" not in request.files:
        return (
            jsonify(
                {
                    "message": "No se encontró el archivo de audio 'audio' en la solicitud."
                }
            ),
            400,
        )

    audio_file = request.files["audio"]
    if audio_file.filename == "":
        return jsonify({"message": "No se seleccionó ningún archivo."}), 400

    # Opcional: El usuario puede especificar un agent_id si quiere usar un agente específico.
    # Si no se proporciona, el servicio intentará usar el agente predeterminado.
    agent_id_str = request.form.get("agent_id")
    agent_id = None
    if agent_id_str:
        try:
            agent_id = uuid.UUID(agent_id_str)
        except ValueError:
            return (
                jsonify(
                    {"message": "El ID del agente proporcionado no es un UUID válido."}
                ),
                400,
            )

    try:
        # TODO: user_id debe provenir del sistema de autenticación real.
        # Para desarrollo, usar un UUID fijo temporalmente:
        user_id = uuid.UUID(
            "a1b2c3d4-e5f6-7890-1234-567890abcdef"
        )  # TEMPORAL para desarrollo

        # Accede a transcribe_service directamente desde la aplicación
        transcription = current_app.transcribe_service.transcribe_audio(
            audio_file, user_id, agent_id
        )

        # Serializar la transcripción para la respuesta JSON
        result = transcription_schema.dump(transcription)
        return jsonify(result), 201

    except ValueError as e:
        logger.warning(f"Error de validación o lógica de negocio en /transcribe: {e}")
        return jsonify({"message": str(e)}), 400
    except RuntimeError as e:
        logger.error(
            f"Error durante el proceso de transcripción o subida a Azure: {e}",
            exc_info=True,
        )
        return jsonify({"message": f"Error en el servicio de transcripción: {e}"}), 500
    except Exception as e:
        logger.exception("Error inesperado en el endpoint /transcribe")
        return (
            jsonify(
                {"message": "Error interno del servidor al procesar la transcripción."}
            ),
            500,
        )


@bp.route("/transcriptions", methods=["GET"])
def get_all_transcriptions():
    """
    Endpoint para obtener una lista de todas las transcripciones.
    """
    try:
        transcriptions = g.transcribe_service.get_all_transcriptions()
        return jsonify(transcriptions_schema.dump(transcriptions)), 200
    except Exception as e:
        logger.exception("Error al obtener todas las transcripciones.")
        return (
            jsonify(
                {"message": "Error interno del servidor al obtener transcripciones."}
            ),
            500,
        )


@bp.route("/transcriptions/<uuid:transcription_id>", methods=["GET"])
def get_transcription(transcription_id: uuid.UUID):
    """
    Endpoint para obtener una transcripción por su ID.
    """
    try:
        transcription = g.transcribe_service.get_transcription_by_id(transcription_id)
        if transcription:
            return jsonify(transcription_schema.dump(transcription)), 200
        return jsonify({"message": "Transcripción no encontrada."}), 404
    except Exception as e:
        logger.exception(f"Error al obtener transcripción con ID {transcription_id}.")
        return (
            jsonify(
                {"message": "Error interno del servidor al obtener transcripción."}
            ),
            500,
        )


@bp.route("/transcriptions/<uuid:transcription_id>", methods=["PATCH"])
def update_transcription(transcription_id: uuid.UUID):
    """
    Endpoint para actualizar una transcripción existente (parcialmente o el contenido de texto).
    """
    try:
        update_data = request.json
        if not update_data:
            return (
                jsonify(
                    {"message": "No se proporcionaron datos para la actualización."}
                ),
                400,
            )

        # Si se quiere actualizar solo el texto, usar el método específico
        if "text_content" in update_data and len(update_data) == 1:
            updated_transcription = (
                g.transcribe_service.update_transcription_text_content(
                    transcription_id, update_data["text_content"]
                )
            )
        else:
            # Para actualizaciones parciales de otros campos, usar el método general de actualización
            updated_transcription = g.transcribe_service.update_transcription(
                transcription_id, update_data
            )

        if updated_transcription:
            return jsonify(transcription_schema.dump(updated_transcription)), 200
        return jsonify({"message": "Transcripción no encontrada."}), 404
    except ValueError as e:
        logger.warning(
            f"Error de validación al actualizar transcripción {transcription_id}: {e}"
        )
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        logger.exception(
            f"Error al actualizar transcripción con ID {transcription_id}."
        )
        return (
            jsonify(
                {"message": "Error interno del servidor al actualizar transcripción."}
            ),
            500,
        )


@bp.route("/transcriptions/<uuid:transcription_id>", methods=["DELETE"])
def delete_transcription(transcription_id: uuid.UUID):
    """
    Endpoint para eliminar una transcripción.
    """
    try:
        if g.transcribe_service.delete_transcription(transcription_id):
            return jsonify({"message": "Transcripción eliminada exitosamente."}), 204
        return jsonify({"message": "Transcripción no encontrada."}), 404
    except Exception as e:
        logger.exception(f"Error al eliminar transcripción con ID {transcription_id}.")
        return (
            jsonify(
                {"message": "Error interno del servidor al eliminar transcripción."}
            ),
            500,
        )
