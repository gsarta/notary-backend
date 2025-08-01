from sqlalchemy.orm import Session
from app.repositories.template_section_composition_repository import (
    TemplateSectionCompositionRepository,
)
from app.schemas.template_section_composition import (
    TemplateSectionCompositionCreateSchema,
    TemplateSectionCompositionUpdateSchema,
    TemplateSectionCompositionSchema,
)
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


class TemplateSectionCompositionService:
    def __init__(self, db_session: Session):
        self.repository = TemplateSectionCompositionRepository(db_session)
        self.schema = TemplateSectionCompositionSchema()
        self.create_schema = TemplateSectionCompositionCreateSchema()
        self.update_schema = TemplateSectionCompositionUpdateSchema()

    def get_all_compositions(self) -> list[dict]:
        """Obtiene todas las composiciones de secciones de plantilla."""
        compositions = self.repository.get_all()
        return [self.schema.dump(c) for c in compositions]

    def get_composition_by_ids(
        self, template_id: UUID, section_id: UUID
    ) -> dict | None:
        """Obtiene una composición de sección por sus IDs de plantilla y sección."""
        composition = self.repository.get_by_ids(template_id, section_id)
        if not composition:
            return None
        return self.schema.dump(composition)

    def get_compositions_by_template_id(self, template_id: UUID) -> list[dict]:
        """Obtiene todas las composiciones para una plantilla específica, ordenadas por order_index."""
        compositions = self.repository.get_by_template_id(template_id)
        return [self.schema.dump(c) for c in compositions]

    def create_composition(self, composition_data: dict) -> dict:
        """Crea una nueva composición de sección de plantilla."""
        errors = self.create_schema.validate(composition_data)
        if errors:
            logger.error(
                f"Errores de validación al crear composición de sección: {errors}"
            )
            raise ValueError(f"Datos de entrada inválidos: {errors}")

        # El repositorio ya maneja las validaciones de unicidad de (template_id, section_id) y (template_id, order_index)
        new_composition = self.repository.create(composition_data)
        return self.schema.dump(new_composition)

    def update_composition(
        self, template_id: UUID, section_id: UUID, update_data: dict
    ) -> dict | None:
        """Actualiza una composición de sección de plantilla existente."""
        errors = self.update_schema.validate(update_data)
        if errors:
            logger.error(
                f"Errores de validación al actualizar composición de sección (template_id: {template_id}, section_id: {section_id}): {errors}"
            )
            raise ValueError(f"Datos de entrada inválidos: {errors}")

        composition = self.repository.get_by_ids(template_id, section_id)
        if not composition:
            return None

        updated_composition = self.repository.update(composition, update_data)
        return self.schema.dump(updated_composition)

    def delete_composition(self, template_id: UUID, section_id: UUID) -> bool:
        """Elimina una composición de sección de plantilla por sus IDs."""
        composition = self.repository.get_by_ids(template_id, section_id)
        if not composition:
            return False
        self.repository.delete(composition)
        return True
