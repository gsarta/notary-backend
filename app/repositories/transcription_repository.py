import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.transcription import (
    Transcription,
)
import uuid

logger = logging.getLogger(__name__)


class TranscriptionRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(self, transcription_data: dict) -> Transcription:
        """
        Añade una nueva transcripción a la base de datos.
        """
        try:
            new_transcription = Transcription(
                audio_url=transcription_data.get("audio_url"),
                text_content=transcription_data.get("text_content"),
                duration_seconds=transcription_data.get("duration_seconds"),
                status=transcription_data.get("status"),
                agent_id=transcription_data.get("agent_id"),
                created_by=transcription_data.get("created_by"),
            )
            self.session.add(new_transcription)
            self.session.commit()
            self.session.refresh(new_transcription)
            logger.info(
                f"Transcripción {new_transcription.transcription_id} añadida exitosamente."
            )
            return new_transcription
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error de base de datos al añadir transcripción: {e}")
            raise RuntimeError(
                f"No se pudo añadir la transcripción debido a un error de DB: {e}"
            )
        except Exception as e:
            self.session.rollback()
            logger.error(
                f"Error inesperado al añadir transcripción: {e}", exc_info=True
            )
            raise RuntimeError(f"Error inesperado al añadir transcripción: {e}")

    def get_by_id(self, transcription_id: uuid.UUID) -> Transcription | None:
        """
        Obtiene una transcripción por su ID.
        """
        try:
            return (
                self.session.query(Transcription)
                .filter_by(transcription_id=transcription_id)
                .first()
            )
        except SQLAlchemyError as e:
            logger.error(
                f"Error de base de datos al obtener transcripción por ID {transcription_id}: {e}"
            )
            raise RuntimeError(f"No se pudo obtener la transcripción: {e}")

    def get_all(self) -> list[Transcription]:
        """
        Obtiene todas las transcripciones.
        """
        try:
            return self.session.query(Transcription).all()
        except SQLAlchemyError as e:
            logger.error(
                f"Error de base de datos al obtener todas las transcripciones: {e}"
            )
            raise RuntimeError(f"No se pudieron obtener las transcripciones: {e}")

    def update(
        self, transcription_id: uuid.UUID, updates: dict
    ) -> Transcription | None:
        """
        Actualiza una transcripción existente por su ID.
        """
        try:
            transcription = (
                self.session.query(Transcription)
                .filter_by(transcription_id=transcription_id)
                .first()
            )
            if transcription:
                for key, value in updates.items():
                    # Solo actualizar atributos que realmente existen en el modelo
                    if hasattr(transcription, key):
                        setattr(transcription, key, value)
                    else:
                        logger.warning(
                            f"Intento de actualizar campo no existente: {key}"
                        )
                self.session.commit()
                logger.info(
                    f"Transcripción {transcription_id} actualizada exitosamente."
                )
                return transcription
            return None
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(
                f"Error de base de datos al actualizar transcripción {transcription_id}: {e}"
            )
            raise RuntimeError(f"No se pudo actualizar la transcripción: {e}")
        except Exception as e:
            self.session.rollback()
            logger.error(
                f"Error inesperado al actualizar transcripción {transcription_id}: {e}",
                exc_info=True,
            )
            raise RuntimeError(f"Error inesperado al actualizar transcripción: {e}")

    def update_text_content(
        self, transcription_id: uuid.UUID, new_text_content: str
    ) -> Transcription | None:
        """
        Actualiza únicamente el contenido de texto de una transcripción por su ID.
        """
        return self.update(transcription_id, {"text_content": new_text_content})

    def delete(self, transcription_id: uuid.UUID) -> bool:
        """
        Elimina una transcripción por su ID.
        """
        try:
            transcription = (
                self.session.query(Transcription)
                .filter_by(transcription_id=transcription_id)
                .first()
            )
            if transcription:
                self.session.delete(transcription)
                self.session.commit()
                logger.info(f"Transcripción {transcription_id} eliminada exitosamente.")
                return True
            return False
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(
                f"Error de base de datos al eliminar transcripción {transcription_id}: {e}"
            )
            raise RuntimeError(f"No se pudo eliminar la transcripción: {e}")
        except Exception as e:
            self.session.rollback()
            logger.error(
                f"Error inesperado al eliminar transcripción {transcription_id}: {e}",
                exc_info=True,
            )
            raise RuntimeError(f"Error inesperado al eliminar transcripción: {e}")
