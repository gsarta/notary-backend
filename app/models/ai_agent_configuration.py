import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Boolean,
    JSON,
    DateTime,
    column,
)
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base


class AIAgentConfiguration(Base):
    __tablename__ = "ai_agent_configurations"
    __table_args__ = {"schema": "notary"}

    agent_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_name = Column(String(100), unique=True, nullable=False)
    provider = Column(
        String(50), nullable=False
    )  # ej. 'OPENAI', 'AWS_BEDROCK', 'GOOGLE_AI'
    model_name = Column(
        String(100), nullable=False
    )  # ej. 'whisper-1', 'claude-3-opus-20240229'
    api_base_url = Column(String(255))
    api_key_secret_name = Column(
        String(100)
    )  # Nombre de la variable de entorno/secreto que contiene la API Key
    config_json = Column(
        JSON, default={}
    )  # Configuraciones adicionales en formato JSON
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)  # Solo uno puede ser TRUE a la vez
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Restricción para asegurar que solo un agente puede ser el predeterminado
    # Usa ExcludeConstraint para una restricción condicional en PostgreSQL
    __table_args__ = (
        ExcludeConstraint(
            (column("is_default"), "="),  # Excluir si 'is_default' es igual
            where=column("is_default") == True,  # ...pero solo si 'is_default' es TRUE
            name="idx_ai_agent_configurations_one_default_agent",
            deferrable=True,  # Para transacciones
            initially="DEFERRED",  # Para transacciones
        ),
        {"schema": "notary"},
    )

    def __repr__(self):
        return f"<AIAgentConfiguration(name='{self.agent_name}', model='{self.model_name}')>"
