from sqlalchemy import Column, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.models.base import (
    Base,
)


class TemplateSection(Base):
    """
    Almacena las secciones de contenido reutilizables para las plantillas.
    """

    __tablename__ = "template_sections"
    __table_args__ = {"schema": "notary"}

    section_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    section_name = Column(String(255), nullable=False, unique=True)
    section_content_template = Column(
        Text, nullable=False
    )  # Contenido base de la sección con placeholders
    variables_schema = Column(
        JSON, nullable=False, default={}
    )  # Esquema JSONB para variables dinámicas
    description = Column(Text, nullable=True)

    # Relación inversa a TemplateSectionComposition
    # 'cascade="all, delete-orphan"' asegura que si una sección se elimina,
    # se eliminen también las entradas de composición que solo la referencian.
    # Nota: Esto es útil para composiciones *que solo referencian esta sección*.
    compositions = relationship(
        "TemplateSectionComposition",
        back_populates="section",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<TemplateSection(id='{self.section_id}', name='{self.section_name}')>"
