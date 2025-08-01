from sqlalchemy.orm import Session
from app.repositories.template_repository import TemplateRepository
from app.schemas.template_schema import (
    TemplateCreateSchema,
    TemplateUpdateSchema,
    TemplateSchema,
)
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


class TemplateService:
    def __init__(self, db_session: Session):
        self.repository = TemplateRepository(db_session)
        self.schema = TemplateSchema()
        self.create_schema = TemplateCreateSchema()
        self.update_schema = TemplateUpdateSchema()

    def get_all_templates(self) -> list[dict]:
        """Obtiene todas las plantillas."""
        templates = self.repository.get_all()
        return [self.schema.dump(t) for t in templates]

    def get_template_by_id(self, template_id: UUID) -> dict | None:
        """Obtiene una plantilla por su ID."""
        template = self.repository.get_by_id(template_id)
        if not template:
            return None
        return self.schema.dump(template)

    def create_template(self, template_data: dict) -> dict:
        """Crea una nueva plantilla."""
        errors = self.create_schema.validate(template_data)
        if errors:
            logger.error(f"Errores de validación al crear plantilla: {errors}")
            raise ValueError(f"Datos de entrada inválidos: {errors}")

        new_template = self.repository.create(template_data)
        return self.schema.dump(new_template)

    def update_template(self, template_id: UUID, update_data: dict) -> dict | None:
        """Actualiza una plantilla existente."""
        errors = self.update_schema.validate(update_data)
        if errors:
            logger.error(
                f"Errores de validación al actualizar plantilla (ID: {template_id}): {errors}"
            )
            raise ValueError(f"Datos de entrada inválidos: {errors}")

        template = self.repository.get_by_id(template_id)
        if not template:
            return None

        # Verificar si el nombre de la plantilla se está actualizando y si entra en conflicto
        if (
            "template_name" in update_data
            and update_data["template_name"] != template.template_name
        ):
            existing_template = self.repository.get_by_name(
                update_data["template_name"]
            )
            if existing_template and existing_template.template_id != template_id:
                raise RuntimeError(
                    "Ya existe otra plantilla con el nombre proporcionado."
                )

        updated_template = self.repository.update(template, update_data)
        return self.schema.dump(updated_template)

    def delete_template(self, template_id: UUID) -> bool:
        """Elimina una plantilla por su ID."""
        template = self.repository.get_by_id(template_id)
        if not template:
            return False

        try:
            self.repository.delete(template)
            return True
        except RuntimeError as e:
            if "Error al eliminar la plantilla." in str(e):
                raise RuntimeError(
                    "No se puede eliminar la plantilla porque está siendo utilizada en composiciones o documentos. Elimine primero sus dependencias."
                )
            raise
