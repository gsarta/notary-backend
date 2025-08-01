from sqlalchemy.orm import Session
from app.repositories.template_section_repository import TemplateSectionRepository
from app.schemas.template_section import (
    TemplateSectionCreateSchema,
    TemplateSectionUpdateSchema,
    TemplateSectionSchema,
)
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


class TemplateSectionService:
    def __init__(self, db_session: Session):
        self.repository = TemplateSectionRepository(db_session)
        self.schema = TemplateSectionSchema()
        self.create_schema = TemplateSectionCreateSchema()
        self.update_schema = TemplateSectionUpdateSchema()

    def get_all_template_sections(self) -> list[dict]:
        """Obtiene todas las secciones de plantilla."""
        sections = self.repository.get_all()
        return [self.schema.dump(s) for s in sections]

    def get_template_section_by_id(self, section_id: UUID) -> dict | None:
        """Obtiene una sección de plantilla por su ID."""
        section = self.repository.get_by_id(section_id)
        if not section:
            return None
        return self.schema.dump(section)

    def create_template_section(self, section_data: dict) -> dict:
        """Crea una nueva sección de plantilla."""
        errors = self.create_schema.validate(section_data)
        if errors:
            logger.error(
                f"Errores de validación al crear sección de plantilla: {errors}"
            )
            raise ValueError(f"Datos de entrada inválidos: {errors}")

        new_section = self.repository.create(section_data)
        return self.schema.dump(new_section)

    def update_template_section(
        self, section_id: UUID, update_data: dict
    ) -> dict | None:
        """Actualiza una sección de plantilla existente."""
        errors = self.update_schema.validate(update_data)
        if errors:
            logger.error(
                f"Errores de validación al actualizar sección de plantilla (ID: {section_id}): {errors}"
            )
            raise ValueError(f"Datos de entrada inválidos: {errors}")

        section = self.repository.get_by_id(section_id)
        if not section:
            return None

        # Si se intenta cambiar el nombre, verificar si el nuevo nombre ya existe en otra sección
        if (
            "section_name" in update_data
            and update_data["section_name"] != section.section_name
        ):
            existing_section_with_name = self.repository.get_by_name(
                update_data["section_name"]
            )
            if (
                existing_section_with_name
                and existing_section_with_name.section_id != section_id
            ):
                raise RuntimeError(
                    "Ya existe otra sección de plantilla con el nombre proporcionado."
                )

        updated_section = self.repository.update(section, update_data)
        return self.schema.dump(updated_section)

    def delete_template_section(self, section_id: UUID) -> bool:
        """Elimina una sección de plantilla por su ID."""
        section = self.repository.get_by_id(section_id)
        if not section:
            return False

        try:
            self.repository.delete(section)
            return True
        except RuntimeError as e:  # Capturar el error propagado desde el repositorio
            # TODO: Refinar el mensaje de error si el repo devuelve mensajes específicos
            if (
                "No se puede eliminar la sección porque está siendo utilizada en una o más plantillas."
                in str(e)
            ):
                raise RuntimeError(
                    "No se puede eliminar la sección porque está siendo utilizada en una o más plantillas. Por favor, elimine primero sus composiciones."
                )
            raise
