from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.template_section_composition import TemplateSectionComposition

import logging
from uuid import UUID

logger = logging.getLogger(__name__)


class TemplateSectionCompositionRepository:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_all(self) -> list[TemplateSectionComposition]:
        """Obtiene todas las composiciones de secciones de plantillas."""
        return self.db_session.query(TemplateSectionComposition).all()

    def get_by_ids(
        self, template_id: UUID, section_id: UUID
    ) -> TemplateSectionComposition | None:
        """Obtiene una composición de sección por su ID de plantilla y su ID de sección (PK compuesto)."""
        return (
            self.db_session.query(TemplateSectionComposition)
            .filter(
                TemplateSectionComposition.template_id == template_id,
                TemplateSectionComposition.section_id == section_id,
            )
            .first()
        )

    def get_by_template_id(self, template_id: UUID) -> list[TemplateSectionComposition]:
        """Obtiene todas las composiciones para una plantilla específica, ordenadas por order_index."""
        return (
            self.db_session.query(TemplateSectionComposition)
            .filter(TemplateSectionComposition.template_id == template_id)
            .order_by(TemplateSectionComposition.order_index)
            .all()
        )

    def create(self, composition_data: dict) -> TemplateSectionComposition:
        """Crea una nueva composición de sección de plantilla."""
        try:
            new_composition = TemplateSectionComposition(**composition_data)
            self.db_session.add(new_composition)
            self.db_session.commit()
            self.db_session.refresh(new_composition)
            return new_composition
        except IntegrityError as e:
            self.db_session.rollback()
            logger.error(
                f"Error de integridad al crear TemplateSectionComposition: {e}"
            )
            # Mensajes específicos para errores de UniqueConstraint
            if "template_sections_composition_template_id_order_index_key" in str(e):
                raise RuntimeError(
                    "Ya existe una sección en esta plantilla con el mismo índice de orden."
                )
            if "template_sections_composition_pkey" in str(e):
                raise RuntimeError(
                    "Ya existe esta combinación de sección y plantilla en la composición."
                )
            raise RuntimeError(
                "Error de integridad al crear la composición de la sección de plantilla."
            )
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error al crear TemplateSectionComposition: {e}")
            raise RuntimeError(
                "Error al crear la composición de la sección de plantilla."
            )

    def update(
        self, composition: TemplateSectionComposition, update_data: dict
    ) -> TemplateSectionComposition:
        """Actualiza una composición de sección de plantilla existente."""
        try:
            for key, value in update_data.items():
                setattr(composition, key, value)
            self.db_session.commit()
            self.db_session.refresh(composition)
            return composition
        except IntegrityError as e:
            self.db_session.rollback()
            logger.error(
                f"Error de integridad al actualizar TemplateSectionComposition (template_id: {composition.template_id}, section_id: {composition.section_id}): {e}"
            )
            if "template_sections_composition_template_id_order_index_key" in str(e):
                raise RuntimeError(
                    "Ya existe otra sección en esta plantilla con el índice de orden especificado."
                )
            raise RuntimeError(
                "Error de integridad al actualizar la composición de la sección de plantilla."
            )
        except Exception as e:
            self.db_session.rollback()
            logger.error(
                f"Error al actualizar TemplateSectionComposition (template_id: {composition.template_id}, section_id: {composition.section_id}): {e}"
            )
            raise RuntimeError(
                "Error al actualizar la composición de la sección de plantilla."
            )

    def delete(self, composition: TemplateSectionComposition):
        """Elimina una composición de sección de plantilla."""
        try:
            self.db_session.delete(composition)
            self.db_session.commit()
        except Exception as e:
            self.db_session.rollback()
            logger.error(
                f"Error al eliminar TemplateSectionComposition (template_id: {composition.template_id}, section_id: {composition.section_id}): {e}"
            )
            raise RuntimeError(
                "Error al eliminar la composición de la sección de plantilla."
            )
