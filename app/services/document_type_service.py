from sqlalchemy.orm import Session
from app.repositories.document_type_repository import DocumentTypeRepository
from app.schemas.document_type_schema import (
    DocumentTypeCreateSchema,
    DocumentTypeUpdateSchema,
    DocumentTypeSchema,
)
from app.models.document_type import (
    DocumentType,
)
import logging
import uuid

logger = logging.getLogger(__name__)


class DocumentTypeService:
    def __init__(self, db_session: Session):
        self.document_type_repo = DocumentTypeRepository(db_session)
        self.document_type_schema = (
            DocumentTypeSchema()
        )  # Para serializar un solo objeto
        self.document_types_schema = DocumentTypeSchema(
            many=True
        )  # Para serializar listas de objetos
        self.create_schema = DocumentTypeCreateSchema()  # Para validar al crear
        self.update_schema = DocumentTypeUpdateSchema()  # Para validar al actualizar

    def get_all_document_types(self) -> list[dict]:
        """Obtiene y serializa todos los tipos de documentos."""
        document_types = self.document_type_repo.get_all()
        return self.document_types_schema.dump(document_types)

    def get_document_type_by_id(self, document_type_id: str) -> dict:
        """Obtiene y serializa un tipo de documento por su ID.
        Lanza ValueError si el ID es inválido o el tipo de documento no se encuentra.
        """
        try:
            document_type_uuid = uuid.UUID(document_type_id)
        except ValueError:
            logger.error(f"ID de tipo de documento inválido: {document_type_id}")
            raise ValueError(
                "ID de tipo de documento inválido. Debe ser un UUID válido."
            )

        document_type = self.document_type_repo.get_by_id(document_type_uuid)
        if not document_type:
            logger.warning(
                f"Tipo de documento con ID '{document_type_id}' no encontrado."
            )
            raise ValueError("Tipo de documento no encontrado.")
        return self.document_type_schema.dump(document_type)

    def create_document_type(self, document_type_data: dict) -> dict:
        """Crea un nuevo tipo de documento después de validar los datos
        y comprobar si el nombre ya existe.
        Lanza ValueError por validación o duplicidad, y RuntimeError por errores internos.
        """
        # Validar entrada con el esquema de creación
        errors = self.create_schema.validate(document_type_data)
        if errors:
            logger.warning(
                f"Errores de validación al crear tipo de documento: {errors}"
            )
            raise ValueError(f"Datos de entrada inválidos: {errors}")

        # Comprobar si ya existe un tipo de documento con el mismo nombre antes de intentar crear
        existing_document_type = self.document_type_repo.get_by_name(
            document_type_data["type_name"]
        )
        if existing_document_type:
            logger.warning(
                f"Intento de crear tipo de documento con nombre duplicado: {document_type_data['type_name']}"
            )
            raise ValueError(
                f"Ya existe un tipo de documento con el nombre '{document_type_data['type_name']}'."
            )

        try:
            new_document_type = self.document_type_repo.create(document_type_data)
            return self.document_type_schema.dump(new_document_type)
        except (
            Exception
        ) as e:  # Captura cualquier error del repositorio (IntegrityError, RuntimeError, etc.)
            logger.error(f"Error al crear tipo de documento en el repositorio: {e}")
            raise RuntimeError(f"Error en el servicio al crear tipo de documento: {e}")

    def update_document_type(self, document_type_id: str, update_data: dict) -> dict:
        """Actualiza un tipo de documento existente después de validar los datos
        y comprobar si el nuevo nombre ya existe.
        Lanza ValueError por ID inválido, no encontrado, validación o duplicidad,
        y RuntimeError por errores internos.
        """
        try:
            document_type_uuid = uuid.UUID(document_type_id)
        except ValueError:
            logger.error(
                f"ID de tipo de documento inválido para actualización: {document_type_id}"
            )
            raise ValueError(
                "ID de tipo de documento inválido. Debe ser un UUID válido."
            )

        # Validar entrada con el esquema de actualización
        errors = self.update_schema.validate(update_data)
        if errors:
            logger.warning(
                f"Errores de validación al actualizar tipo de documento (ID: {document_type_id}): {errors}"
            )
            raise ValueError(f"Datos de entrada inválidos para actualización: {errors}")

        document_type = self.document_type_repo.get_by_id(document_type_uuid)
        if not document_type:
            logger.warning(
                f"Tipo de documento con ID '{document_type_id}' no encontrado para actualización."
            )
            raise ValueError("Tipo de documento no encontrado.")

        # Comprobar si el nuevo nombre ya existe y no pertenece al mismo tipo de documento que estamos actualizando
        if (
            "type_name" in update_data
            and update_data["type_name"] != document_type.type_name
        ):
            existing_document_type = self.document_type_repo.get_by_name(
                update_data["type_name"]
            )
            if (
                existing_document_type
                and existing_document_type.document_type_id != document_type_uuid
            ):
                logger.warning(
                    f"Intento de actualizar tipo de documento (ID: {document_type_id}) a nombre duplicado: {update_data['type_name']}"
                )
                raise ValueError(
                    f"Ya existe otro tipo de documento con el nombre '{update_data['type_name']}'."
                )

        try:
            updated_document_type = self.document_type_repo.update(
                document_type, update_data
            )
            return self.document_type_schema.dump(updated_document_type)
        except Exception as e:  # Captura cualquier error del repositorio
            logger.error(
                f"Error al actualizar tipo de documento en el repositorio (ID: {document_type_id}): {e}"
            )
            raise RuntimeError(
                f"Error en el servicio al actualizar tipo de documento: {e}"
            )

    def delete_document_type(self, document_type_id: str):
        """Elimina un tipo de documento por su ID.
        Lanza ValueError si el ID es inválido o el tipo de documento no se encuentra,
        y RuntimeError por errores internos.
        """
        try:
            document_type_uuid = uuid.UUID(document_type_id)
        except ValueError:
            logger.error(
                f"ID de tipo de documento inválido para eliminación: {document_type_id}"
            )
            raise ValueError(
                "ID de tipo de documento inválido. Debe ser un UUID válido."
            )

        document_type = self.document_type_repo.get_by_id(document_type_uuid)
        if not document_type:
            logger.warning(
                f"Tipo de documento con ID '{document_type_id}' no encontrado para eliminación."
            )
            raise ValueError("Tipo de documento no encontrado.")

        try:
            self.document_type_repo.delete(document_type)
            logger.info(
                f"Tipo de documento con ID '{document_type_id}' eliminado exitosamente."
            )
        except Exception as e:
            logger.error(
                f"Error al eliminar tipo de documento en el repositorio (ID: {document_type_id}): {e}"
            )
            raise RuntimeError(
                f"Error en el servicio al eliminar tipo de documento: {e}"
            )
