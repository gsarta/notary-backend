from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID
import logging

from app.models.document import Document

logger = logging.getLogger(__name__)


class DocumentRepository:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_all(self) -> list[Document]:
        """Obtiene todos los documentos."""
        try:
            return self.db_session.query(Document).all()
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener todos los documentos: {e}")
            raise RuntimeError(
                f"Error al obtener todos los documentos de la base de datos."
            )

    def get_by_id(self, document_id: UUID) -> Document | None:
        """Obtiene un documento por su ID."""
        try:
            return (
                self.db_session.query(Document)
                .filter(Document.document_id == document_id)
                .first()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener documento con ID {document_id}: {e}")
            raise RuntimeError(
                f"Error al obtener documento de la base de datos con ID {document_id}."
            )

    def create(self, document_data: dict) -> Document:
        """Crea un nuevo documento."""
        try:
            new_document = Document(**document_data)
            self.db_session.add(new_document)
            self.db_session.commit()
            self.db_session.refresh(new_document)
            return new_document
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(f"Error al crear documento: {e}")
            raise RuntimeError(f"Error al crear el documento en la base de datos: {e}")

    def update(self, document: Document, update_data: dict) -> Document:
        """Actualiza un documento existente."""
        try:
            for key, value in update_data.items():
                setattr(document, key, value)
            self.db_session.commit()
            self.db_session.refresh(document)
            return document
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(
                f"Error al actualizar documento con ID {document.document_id}: {e}"
            )
            raise RuntimeError(
                f"Error al actualizar el documento en la base de datos: {e}"
            )

    def delete(self, document: Document) -> None:
        """Elimina un documento."""
        try:
            self.db_session.delete(document)
            self.db_session.commit()
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(
                f"Error al eliminar documento con ID {document.document_id}: {e}"
            )
            raise RuntimeError(
                f"Error al eliminar el documento de la base de datos: {e}"
            )
