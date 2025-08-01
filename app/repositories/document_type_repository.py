from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.document_type import (
    DocumentType,
)
import logging
import uuid

logger = logging.getLogger(__name__)


class DocumentTypeRepository:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_all(self) -> list[DocumentType]:
        """Obtiene todas los tipos de documentos."""
        return self.db_session.query(DocumentType).all()

    def get_by_id(self, document_type_id: uuid.UUID) -> DocumentType | None:
        """Obtiene un tipo de documento por su ID."""
        return (
            self.db_session.query(DocumentType)
            .filter_by(document_type_id=document_type_id)
            .first()
        )

    def get_by_name(self, type_name: str) -> DocumentType | None:
        """Obtiene un tipo de documento por su nombre.
        Lanza RuntimeError en caso de error de base de datos.
        """
        try:
            return (
                self.db_session.query(DocumentType)
                .filter_by(type_name=type_name)
                .first()
            )
        except Exception as e:
            logger.error(
                f"Error de base de datos al obtener tipo de documento por nombre '{type_name}': {e}"
            )
            raise RuntimeError(f"No se pudo obtener el tipo de documento: {e}")

    def create(self, document_type_data: dict) -> DocumentType:
        """Crea un nuevo tipo de documento en la base de datos.
        Lanza ValueError si el nombre del tipo de documento ya existe (IntegrityError).
        Lanza RuntimeError en caso de otros errores de base de datos.
        """
        new_document_type = DocumentType(
            type_name=document_type_data["type_name"],
            description=document_type_data.get("description"),
        )
        self.db_session.add(new_document_type)
        try:
            self.db_session.commit()
            self.db_session.refresh(new_document_type)
            logger.info(
                f"Tipo de documento '{new_document_type.type_name}' creado exitosamente."
            )
            return new_document_type
        except IntegrityError as e:
            self.db_session.rollback()

            if "document_types_type_name_key" in str(e):
                logger.warning(
                    f"Intento de crear tipo de documento con nombre duplicado: {document_type_data['type_name']}"
                )
                raise ValueError(
                    f"Ya existe un tipo de documento con el nombre '{document_type_data['type_name']}'."
                )
            logger.error(f"Error de integridad al crear tipo de documento: {e}")
            raise RuntimeError(
                f"Error de base de datos al crear tipo de documento: {e}"
            )
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error inesperado al crear tipo de documento: {e}")
            raise RuntimeError(f"Error inesperado al crear tipo de documento: {e}")

    def update(self, document_type: DocumentType, update_data: dict) -> DocumentType:
        """Actualiza un tipo de documento existente.
        Lanza ValueError si el nombre del tipo de documento ya existe (IntegrityError).
        Lanza RuntimeError en caso de otros errores de base de datos.
        """
        for key, value in update_data.items():
            setattr(document_type, key, value)
        try:
            self.db_session.commit()
            self.db_session.refresh(document_type)
            logger.info(
                f"Tipo de documento '{document_type.type_name}' actualizado exitosamente."
            )
            return document_type
        except IntegrityError as e:
            self.db_session.rollback()
            if "document_types_type_name_key" in str(e):
                logger.warning(
                    f"Intento de actualizar tipo de documento con nombre duplicado: {document_type.type_name}"
                )
                raise ValueError(
                    f"Ya existe un tipo de documento con el nombre '{document_type.type_name}'."
                )
            logger.error(f"Error de integridad al actualizar tipo de documento: {e}")
            raise RuntimeError(
                f"Error de base de datos al actualizar tipo de documento: {e}"
            )
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error inesperado al actualizar tipo de documento: {e}")
            raise RuntimeError(f"Error inesperado al actualizar tipo de documento: {e}")

    def delete(self, document_type: DocumentType):
        """Elimina un tipo de documento de la base de datos.
        Lanza RuntimeError en caso de error de base de datos.
        """
        try:
            self.db_session.delete(document_type)
            self.db_session.commit()
            logger.info(
                f"Tipo de documento '{document_type.type_name}' eliminado exitosamente."
            )
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error al eliminar tipo de documento: {e}")
            raise RuntimeError(
                f"Error de base de datos al eliminar tipo de documento: {e}"
            )
