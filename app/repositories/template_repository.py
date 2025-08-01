from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.template import Template

import logging
import uuid

logger = logging.getLogger(__name__)


class TemplateRepository:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_all(self) -> list[Template]:
        return self.db_session.query(Template).all()

    def get_by_id(self, template_id: uuid.UUID) -> Template | None:
        return (
            self.db_session.query(Template).filter_by(template_id=template_id).first()
        )

    def get_by_name(self, template_name: str) -> Template | None:
        try:
            return (
                self.db_session.query(Template)
                .filter_by(template_name=template_name)
                .first()
            )
        except Exception as e:
            logger.error(
                f"Error de base de datos al obtener plantilla por nombre {template_name}: {e}"
            )
            raise RuntimeError(f"No se pudo obtener la plantilla: {e}")

    def create(self, template_data: dict) -> Template:
        new_template = Template(
            template_name=template_data["template_name"],
            description=template_data["description"],
            document_type_id=template_data.get("document_type_id"),
            is_active=template_data.get("is_active", True),
            created_by=template_data["created_by"],
        )
        self.db_session.add(new_template)
        try:
            self.db_session.commit()
            self.db_session.refresh(new_template)
            logger.info(
                f"Plantilla '{new_template.template_name}' creada exitosamente."
            )
            return new_template
        except IntegrityError as e:
            self.db_session.rollback()
            if "templates_template_name_key" in str(e):
                logger.warning(
                    f"Intento de crear plantilla con nombre duplicado: {template_data['template_name']}"
                )
                raise ValueError(
                    f"Ya existe una plantilla con el nombre '{template_data['template_name']}'."
                )
            logger.error(f"Error de integridad al crear plantilla: {e}")
            raise RuntimeError(f"Error de base de datos al crear plantilla: {e}")
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error inesperado al crear plantilla: {e}")
            raise RuntimeError(f"Error inesperado al crear plantilla: {e}")

    def update(self, template: Template, update_data: dict) -> Template:
        for key, value in update_data.items():
            if key == "description":
                setattr(template, key, value)
            elif hasattr(template, key):
                setattr(template, key, value)
        try:
            self.db_session.commit()
            self.db_session.refresh(template)
            logger.info(
                f"Plantilla '{template.template_name}' actualizada exitosamente."
            )
            return template
        except IntegrityError as e:
            self.db_session.rollback()
            if "templates_template_name_key" in str(e):
                logger.warning(
                    f"Intento de actualizar plantilla con nombre duplicado: {template.template_name}"
                )
                raise ValueError(
                    f"Ya existe una plantilla con el nombre '{template.template_name}'."
                )
            logger.error(f"Error de integridad al actualizar plantilla: {e}")
            raise RuntimeError(f"Error de base de datos al actualizar plantilla: {e}")
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error inesperado al actualizar plantilla: {e}")
            raise RuntimeError(f"Error inesperado al actualizar plantilla: {e}")

    def delete(self, template: Template):
        try:
            self.db_session.delete(template)
            self.db_session.commit()
            logger.info(f"Plantilla '{template.template_name}' eliminada exitosamente.")
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error al eliminar plantilla: {e}")
            raise RuntimeError(f"Error de base de datos al eliminar plantilla: {e}")
