import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import Base
from app.models.document_type import DocumentType
from app.models.users import User
from app.models.template_section_composition import TemplateSectionComposition


class Template(Base):
    __tablename__ = "templates"
    __table_args__ = {"schema": "notary"}

    template_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    document_type_id = Column(
        UUID(as_uuid=True),
        ForeignKey("notary.document_types.document_type_id"),
        nullable=True,
    )
    is_active = Column(Boolean, default=True)
    created_by = Column(
        UUID(as_uuid=True), ForeignKey("notary.users.user_id"), nullable=True
    )
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(
        DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow()
    )
    document_type = relationship("DocumentType", back_populates="templates")
    section_compositions = relationship(
        "TemplateSectionComposition",
        back_populates="template",
        cascade="all, delete-orphan",
    )
    creator = relationship("User", back_populates="templates_created")
    documents = relationship("Document", back_populates="template")

    def __repr__(self):
        return f"<Template(template_name='{self.template_name}', template_id='{self.template_id}')>"
