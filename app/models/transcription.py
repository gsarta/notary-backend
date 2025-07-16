import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import Base


class Transcription(Base):
    __tablename__ = "transcriptions"
    __table_args__ = {"schema": "notary"}

    transcription_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audio_url = Column(String(255), nullable=False)
    text_content = Column(Text, nullable=False)
    duration_seconds = Column(Integer)
    status = Column(
        String(50), nullable=False, default="completed"
    )  # 'pending', 'completed', 'failed'

    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("notary.ai_agent_configurations.agent_id", ondelete="SET NULL"),
    )
    ai_agent = relationship("AIAgentConfiguration")

    created_by = Column(
        UUID(as_uuid=True), ForeignKey("notary.users.user_id", ondelete="SET NULL")
    )
    user = relationship("User")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Transcription(id='{self.transcription_id}', status='{self.status}')>"
