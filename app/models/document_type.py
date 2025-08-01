from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.models.base import (
    Base,
)


class DocumentType(Base):
    __tablename__ = "document_types"
    __table_args__ = {"schema": "notary"}

    document_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type_name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relaciones (se definirá la relación inversa en el modelo Document)
    documents = relationship("Document", back_populates="document_type")
    templates = relationship("Template", back_populates="document_type")

    def __repr__(self):
        return f"<DocumentType(id={self.document_type_id}, name='{self.type_name}')>"
