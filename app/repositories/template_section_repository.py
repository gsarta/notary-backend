from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.template_section import TemplateSection

import logging
from uuid import UUID

logger = logging.getLogger(__name__)


class TemplateSectionRepository:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_all(self) -> list[TemplateSection]:
        """Obtiene todos los TemplateSection."""
        return self.db_session.query(TemplateSection).all()

    def get_by_id(self, section_id: UUID) -> TemplateSection | None:
        """Obtiene un TemplateSection por su ID."""
        return (
            self.db_session.query(TemplateSection)
            .filter(TemplateSection.section_id == section_id)
            .first()
        )

    def get_by_name(self, section_name: str) -> TemplateSection | None:
        """Obtiene un TemplateSection por su nombre."""
        return (
            self.db_session.query(TemplateSection)
            .filter(TemplateSection.section_name == section_name)
            .first()
        )

    def create(self, template_section_data: dict) -> TemplateSection:
        """Crea un nuevo TemplateSection."""
        try:
            new_section = TemplateSection(**template_section_data)
            self.db_session.add(new_section)
            self.db_session.commit()
            self.db_session.refresh(new_section)
            return new_section
        except IntegrityError as e:
            self.db_session.rollback()
            logger.error(f"Error de integridad al crear TemplateSection: {e}")
            # Detecta si el error es por una restricción UNIQUE (ej. section_name)
            if "duplicate key value violates unique constraint" in str(e).lower():
                raise RuntimeError(
                    "Ya existe una sección de plantilla con este nombre."
                )
            raise RuntimeError("Error de integridad al crear la sección de plantilla.")
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error al crear TemplateSection: {e}")
            raise RuntimeError("Error al crear la sección de plantilla.")

    def update(self, section: TemplateSection, update_data: dict) -> TemplateSection:
        """Actualiza un TemplateSection existente."""
        try:
            for key, value in update_data.items():
                setattr(section, key, value)
            self.db_session.commit()
            self.db_session.refresh(section)
            return section
        except IntegrityError as e:
            self.db_session.rollback()
            logger.error(
                f"Error de integridad al actualizar TemplateSection (ID: {section.section_id}): {e}"
            )
            if "duplicate key value violates unique constraint" in str(e).lower():
                raise RuntimeError(
                    "Ya existe una sección de plantilla con el nombre proporcionado."
                )
            raise RuntimeError(
                "Error de integridad al actualizar la sección de plantilla."
            )
        except Exception as e:
            self.db_session.rollback()
            logger.error(
                f"Error al actualizar TemplateSection (ID: {section.section_id}): {e}"
            )
            raise RuntimeError("Error al actualizar la sección de plantilla.")

    def delete(self, section: TemplateSection):
        """Elimina un TemplateSection."""
        try:
            self.db_session.delete(section)
            self.db_session.commit()
        except Exception as e:
            self.db_session.rollback()
            logger.error(
                f"Error al eliminar TemplateSection (ID: {section.section_id}): {e}"
            )
            raise RuntimeError("Error al eliminar la sección de plantilla.")
