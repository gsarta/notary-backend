import os
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from werkzeug.datastructures import FileStorage
from pydub import AudioSegment
from flask import current_app

from app.utils.audio_processor import AudioProcessor
from app.utils.azure_blob_manager import AzureBlobManager
from app.models.transcription import Transcription
from app.repositories.ai_agent_configuration_repository import (
    AIAgentConfigurationRepository,
)
from app.repositories.transcription_repository import TranscriptionRepository
from app.models.ai_agent_configuration import AIAgentConfiguration

import logging

logger = logging.getLogger(__name__)


class TranscribeService:
    def __init__(
        self,
        db_session: Session,
        audio_processor: AudioProcessor,
        azure_blob_manager: AzureBlobManager,
        segment_duration_ms: int,
    ):
        self.db_session = db_session
        self.audio_processor = audio_processor
        self.azure_blob_manager = azure_blob_manager
        self.ai_agent_repo = AIAgentConfigurationRepository(db_session)
        self.transcription_repo = TranscriptionRepository(db_session)
        self.default_segment_duration_ms = segment_duration_ms  # Desde config.py

    def transcribe_audio(
        self,
        audio_file: FileStorage,
        user_id: uuid.UUID,
        agent_id: uuid.UUID | None = None,
    ) -> Transcription:
        """
        Procesa la transcripción de un archivo de audio, sube el original a Azure Blob Storage,
        y guarda los resultados en la base de datos, asociando un agente de IA.
        """
        if not audio_file or audio_file.filename == "":
            raise ValueError("No se proporcionó ningún archivo de audio válido.")

        # 1. Validar y seleccionar el agente de IA
        selected_agent: AIAgentConfiguration | None = None
        if agent_id:
            selected_agent = self.ai_agent_repo.get_by_id(agent_id)
            if not selected_agent:
                raise ValueError(
                    f"El agente de IA con ID '{agent_id}' no fue encontrado."
                )
            if not selected_agent.is_active:
                raise ValueError(
                    f"El agente de IA '{selected_agent.agent_name}' no está activo."
                )
        else:
            selected_agent = self.ai_agent_repo.get_default_agent()
            if not selected_agent:
                raise ValueError(
                    "No se especificó un agente de IA y no hay un agente predeterminado activo configurado."
                )

        # Verificar que el agente seleccionado sea compatible con la transcripción (ej. OpenAI Whisper)
        if (
            selected_agent.provider != "OPENAI"
            or selected_agent.model_name != "whisper-1"
        ):
            # TODO: Aquí se podría extender la lógica para otros proveedores de transcripción en el futuro
            raise ValueError(
                f"El agente '{selected_agent.agent_name}' ({selected_agent.provider}/{selected_agent.model_name}) no es compatible con la transcripción de Whisper."
            )

        # Obtener la duración del segmento de configuración del agente o usar la predeterminada
        segment_duration_ms_for_agent = selected_agent.config_json.get(
            "segment_duration_ms"
        )
        if segment_duration_ms_for_agent is None:
            segment_duration_ms_for_agent = self.default_segment_duration_ms
            logger.info(
                f"Usando duración de segmento predeterminada de config: {segment_duration_ms_for_agent}ms para agente '{selected_agent.agent_name}'."
            )
        else:
            logger.info(
                f"Usando duración de segmento de configuración del agente: {segment_duration_ms_for_agent}ms para agente '{selected_agent.agent_name}'."
            )

        temp_file_path = None
        try:
            # Generar un nombre de archivo único para evitar colisiones
            filename = f"{uuid.uuid4()}_{audio_file.filename}"
            # Usar un directorio temporal seguro, preferiblemente fuera del control de versiones
            temp_dir = current_app.config.get(
                "UPLOAD_FOLDER", "/tmp"
            )  # Configurar UPLOAD_FOLDER en Config si es diferente
            os.makedirs(temp_dir, exist_ok=True)
            temp_file_path = os.path.join(temp_dir, filename)
            audio_file.save(temp_file_path)
            logger.info(f"Archivo de audio guardado temporalmente en: {temp_file_path}")

            # 2. Subir el archivo de audio original a Azure Blob Storage
            blob_name = f"audios/{user_id}/{filename}"  # Organizar por usuario
            audio_url = self.azure_blob_manager.upload_blob(temp_file_path, blob_name)

            # 3. Obtener duración del audio (para guardar en la BD)
            audio_segment = AudioSegment.from_file(temp_file_path)
            duration_seconds = int(audio_segment.duration_seconds)

            # 4. Transcribir el audio usando el procesador de audio
            transcribed_text = self.audio_processor.transcribe_audio_with_whisper(
                temp_file_path, segment_duration_ms=segment_duration_ms_for_agent
            )

            # 5. Guardar la transcripción en la base de datos
            transcription = Transcription(
                audio_url=audio_url,
                text_content=transcribed_text,
                duration_seconds=duration_seconds,
                status="completed",
                agent_id=selected_agent.agent_id,  # Asociar el ID del agente utilizado
                created_by=user_id,  # Asociar el ID del usuario
            )
            self.db_session.add(transcription)
            self.db_session.commit()
            self.db_session.refresh(
                transcription
            )  # Para obtener el transcription_id generado

            logger.info(
                f"Transcripción {transcription.transcription_id} guardada exitosamente."
            )
            return transcription

        except ValueError as e:
            self.db_session.rollback()  # Revertir la transacción si hay un error
            logger.warning(
                f"Error de validación o configuración en TranscribeService: {e}"
            )
            raise  # Re-lanzar para que el controlador lo maneje
        except RuntimeError as e:
            self.db_session.rollback()
            logger.error(
                f"Error de servicio externo (OpenAI/Azure) durante la transcripción: {e}",
                exc_info=True,
            )
            raise  # Re-lanzar
        except Exception as e:
            self.db_session.rollback()
            logger.error(
                f"Error inesperado durante el proceso de transcripción: {e}",
                exc_info=True,
            )
            raise RuntimeError(
                f"Error interno del servidor durante la transcripción: {e}"
            )
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)  # Limpiar el archivo temporal
                logger.info(f"Archivo temporal eliminado: {temp_file_path}")

    def get_all_transcriptions(self) -> list[Transcription]:
        """Obtiene todas las transcripciones."""
        return self.transcription_repo.get_all()

    def get_transcription_by_id(
        self, transcription_id: uuid.UUID
    ) -> Transcription | None:
        """Obtiene una transcripción por su ID."""
        return self.transcription_repo.get_by_id(transcription_id)

    def update_transcription(
        self, transcription_id: uuid.UUID, update_data: dict
    ) -> Transcription | None:
        """Actualiza una transcripción existente."""
        return self.transcription_repo.update(transcription_id, update_data)

    def update_transcription_text_content(
        self, transcription_id: uuid.UUID, new_text_content: str
    ) -> Transcription | None:
        """Actualiza solo el contenido de texto de una transcripción."""
        return self.transcription_repo.update_text_content(
            transcription_id, new_text_content
        )

    def delete_transcription(self, transcription_id: uuid.UUID) -> bool:
        """Elimina una transcripción por su ID."""
        return self.transcription_repo.delete(transcription_id)
