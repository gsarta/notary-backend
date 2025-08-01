from sqlalchemy import Column, Integer, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import (
    Base,
)


class TemplateSectionComposition(Base):
    """
    Define la relación muchos a muchos entre plantillas y secciones, incluyendo orden y obligatoriedad.
    """

    __tablename__ = "template_sections_composition"
    __table_args__ = (
        UniqueConstraint(
            "template_id",
            "order_index",
            name="template_sections_composition_template_id_order_index_key",
        ),
        {"schema": "notary"},
    )

    template_id = Column(
        UUID(as_uuid=True),
        ForeignKey("notary.templates.template_id", ondelete="CASCADE"),
        primary_key=True,
    )
    section_id = Column(
        UUID(as_uuid=True),
        ForeignKey("notary.template_sections.section_id", ondelete="RESTRICT"),
        primary_key=True,
    )
    order_index = Column(Integer, nullable=False)
    is_mandatory = Column(Boolean, nullable=False, default=True)

    # Relaciones con las tablas Template y TemplateSection
    template = relationship("Template", back_populates="section_compositions")
    section = relationship("TemplateSection", back_populates="compositions")

    def __repr__(self):
        return f"<TemplateSectionComposition(template_id='{self.template_id}', section_id='{self.section_id}', order_index={self.order_index})>"
