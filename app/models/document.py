from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.models.base import (
    Base,
)


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = {"schema": "notary"}

    document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_name = Column(String(255), nullable=False)
    document_type_id = Column(
        UUID(as_uuid=True),
        ForeignKey("notary.document_types.document_type_id", ondelete="SET NULL"),
        nullable=True,
    )
    template_id = Column(
        UUID(as_uuid=True),
        ForeignKey("notary.templates.template_id", ondelete="SET NULL"),
        nullable=True,
    )
    text_content = Column(Text, nullable=False)
    pdf_url = Column(String(255), nullable=True)
    dynamic_data = Column(JSONB, nullable=False, default={})
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("notary.users.user_id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # back_populates creará la relación inversa en el modelo relacionado
    document_type = relationship("DocumentType", back_populates="documents")
    template = relationship("Template", back_populates="documents")

    def __repr__(self):
        return f"<Document(id={self.document_id}, name='{self.document_name}', type_id={self.document_type_id})>"
