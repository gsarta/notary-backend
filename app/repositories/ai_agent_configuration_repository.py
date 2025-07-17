from sqlalchemy.orm import Session
from app.models.ai_agent_configuration import AIAgentConfiguration
import uuid
import logging

logger = logging.getLogger(__name__)


class AIAgentConfigurationRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, agent_id: uuid.UUID) -> AIAgentConfiguration | None:
        # Obtiene un agente de IA por su ID
        return (
            self.session.query(AIAgentConfiguration)
            .filter_by(agent_id=agent_id)
            .first()
        )

    def get_default_agent(self) -> AIAgentConfiguration | None:
        # Obtiene el agente de IA predeterminado activo
        return (
            self.session.query(AIAgentConfiguration)
            .filter_by(is_default=True, is_active=True)
            .first()
        )

    def create(self, agent_data: dict) -> AIAgentConfiguration:
        # Crea un nuevo agente de IA.
        try:
            agent = AIAgentConfiguration(**agent_data)
            self.session.add(agent)
            self.session.commit()
            self.session.refresh(agent)
            logger.info(
                f"Agente de IA '{agent.agent_name}' creado con ID: {agent.agent_id}"
            )
            return agent
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error al crear agente de IA: {e}", exc_info=True)
            raise RuntimeError(f"Error de base de datos al crear agente de IA: {e}")

    def update(
        self, agent_id: uuid.UUID, update_data: dict
    ) -> AIAgentConfiguration | None:
        # Actualiza un agente de IA existente.
        try:
            agent = self.get_by_id(agent_id)
            if agent:
                for key, value in update_data.items():
                    setattr(agent, key, value)
                self.session.commit()
                self.session.refresh(agent)
                logger.info(
                    f"Agente de IA '{agent.agent_name}' (ID: {agent_id}) actualizado."
                )
            return agent
        except Exception as e:
            self.session.rollback()
            logger.error(
                f"Error al actualizar agente de IA con ID {agent_id}: {e}",
                exc_info=True,
            )
            raise RuntimeError(
                f"Error de base de datos al actualizar agente de IA: {e}"
            )

    def delete(self, agent_id: uuid.UUID) -> bool:
        # Elimina un agente de IA.
        try:
            agent = self.get_by_id(agent_id)
            if agent:
                self.session.delete(agent)
                self.session.commit()
                logger.info(f"Agente de IA con ID {agent_id} eliminado.")
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(
                f"Error al eliminar agente de IA con ID {agent_id}: {e}", exc_info=True
            )
            raise RuntimeError(f"Error de base de datos al eliminar agente de IA: {e}")

    def get_all(self) -> list[AIAgentConfiguration]:
        # Obtiene todos los agentes de IA.
        return self.session.query(AIAgentConfiguration).all()

    def unset_all_defaults(self):
        # Desactiva el estado 'is_default' para todos los agentes activos.
        try:
            self.session.query(AIAgentConfiguration).filter(
                AIAgentConfiguration.is_default == True
            ).update({"is_default": False})
            self.session.commit()
            logger.info(
                "Estado 'is_default' desactivado para todos los agentes previamente predeterminados."
            )
        except Exception as e:
            self.session.rollback()
            logger.error(
                f"Error al desactivar agentes predeterminados: {e}", exc_info=True
            )
            raise RuntimeError(
                f"Error de base de datos al desactivar agentes predeterminados: {e}"
            )
