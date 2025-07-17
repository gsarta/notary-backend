from sqlalchemy.orm import Session
from app.repositories.ai_agent_configuration_repository import (
    AIAgentConfigurationRepository,
)
from app.models.ai_agent_configuration import AIAgentConfiguration
import uuid
import logging

logger = logging.getLogger(__name__)


class AIAgentConfigurationService:
    def __init__(self, db_session: Session):
        self.repo = AIAgentConfigurationRepository(db_session)
        self.db_session = db_session

    def get_all_agents(self) -> list[AIAgentConfiguration]:
        """Obtiene todas las configuraciones de agentes de IA."""
        return self.repo.get_all()

    def get_agent_by_id(self, agent_id: uuid.UUID) -> AIAgentConfiguration | None:
        """Obtiene una configuración de agente de IA por su ID."""
        return self.repo.get_by_id(agent_id)

    def create_agent(self, agent_data: dict) -> AIAgentConfiguration:
        """
        Crea un nuevo agente de IA. Asegura que solo un agente sea el predeterminado si se marca como tal.
        """
        try:
            if agent_data.get("is_default"):
                self.repo.unset_all_defaults()  # Desactiva otros por defecto
            return self.repo.create(agent_data)
        except Exception as e:
            logger.error(f"Servicio: Error al crear agente de IA: {e}")
            raise  # Re-lanzar para que el controlador maneje el error

    def update_agent(
        self, agent_id: uuid.UUID, update_data: dict
    ) -> AIAgentConfiguration | None:
        """
        Actualiza una configuración de agente de IA existente.
        Maneja la lógica para el agente predeterminado, forzando la asignación si el actual se desactiva.
        """
        agent = self.repo.get_by_id(agent_id)
        if not agent:
            return None

        # Lógica para manejar el cambio de is_default
        if "is_default" in update_data:
            if update_data["is_default"] and not agent.is_default:
                # Si se está intentando hacer este agente el nuevo default
                self.repo.unset_all_defaults()
            elif not update_data["is_default"] and agent.is_default:
                # Si el agente actual predeterminado se está desmarcando
                logger.info(
                    f"Agente {agent_id} desmarcado como predeterminado. Intentando asignar un nuevo default..."
                )
                # Intentar encontrar otro agente activo para ser el nuevo predeterminado
                # Primero, obtener todos los agentes activos excepto el que se está desmarcando
                all_active_agents = (
                    self.repo.session.query(AIAgentConfiguration)
                    .filter(
                        AIAgentConfiguration.is_active == True,
                        AIAgentConfiguration.agent_id
                        != agent_id,  # Excluir el agente actual
                    )
                    .all()
                )

                new_default_found = False
                for other_agent in all_active_agents:
                    # Encontrar el primer agente activo que no sea el actual y hacerlo default
                    if (
                        not other_agent.is_default
                    ):  # Asegurarse de que no sea ya un default (aunque unset_all_defaults lo manejaría)
                        other_agent.is_default = True
                        self.repo.session.add(other_agent)
                        self.db_session.commit()  # Confirmar el cambio en el nuevo default
                        logger.info(
                            f"Nuevo agente predeterminado asignado: '{other_agent.agent_name}' (ID: {other_agent.agent_id})"
                        )
                        new_default_found = True
                        break  # Se encontró y asignó un nuevo default, salir del bucle

                if not new_default_found and len(all_active_agents) > 0:
                    # Si no se encontró un nuevo default entre los demás agentes activos
                    # Esto podría ocurrir si todos los demás agentes activos ya eran "no-default"
                    # y no se les marcó explícitamente como default arriba.
                    # Aquí la lógica es forzar que el PRIMERO disponible se convierta en default.
                    first_available_agent = all_active_agents[0]
                    first_available_agent.is_default = True
                    self.repo.session.add(first_available_agent)
                    self.db_session.commit()
                    logger.info(
                        f"Forzando asignación de nuevo agente predeterminado: '{first_available_agent.agent_name}' (ID: {first_available_agent.agent_id})"
                    )
                    new_default_found = True  # Redundante, pero asegura el estado

                if not new_default_found:
                    # Si no se pudo asignar un nuevo default (porque no hay otros agentes activos)
                    self.db_session.rollback()  # Revertir cambios si no se puede asegurar un default
                    error_msg = f"No se pudo desmarcar el agente predeterminado '{agent.agent_name}' (ID: {agent_id}) porque no hay otro agente activo para asignar como predeterminado."
                    logger.error(error_msg)
                    raise ValueError(error_msg)

        try:
            # Finalmente, actualizar el agente original
            return self.repo.update(agent_id, update_data)
        except Exception as e:
            logger.error(f"Servicio: Error al actualizar agente de IA {agent_id}: {e}")
            raise  # Re-lanzar

    def delete_agent(self, agent_id: uuid.UUID) -> bool:
        """Elimina una configuración de agente de IA."""
        try:
            # Antes de eliminar, verificar si es el agente predeterminado
            agent = self.repo.get_by_id(agent_id)
            if agent and agent.is_default:
                logger.info(
                    f"Agente {agent_id} (predeterminado) está siendo eliminado. Intentando asignar un nuevo default..."
                )

                # Intentar encontrar otro agente activo para ser el nuevo predeterminado
                all_active_agents = (
                    self.repo.session.query(AIAgentConfiguration)
                    .filter(
                        AIAgentConfiguration.is_active == True,
                        AIAgentConfiguration.agent_id
                        != agent_id,  # Excluir el agente que se va a eliminar
                    )
                    .all()
                )

                new_default_found = False
                if all_active_agents:
                    # Asignar el primer agente activo como nuevo default
                    first_available_agent = all_active_agents[0]
                    first_available_agent.is_default = True
                    self.repo.session.add(first_available_agent)
                    self.db_session.commit()
                    logger.info(
                        f"Nuevo agente predeterminado asignado tras eliminación: '{first_available_agent.agent_name}' (ID: {first_available_agent.agent_id})"
                    )
                    new_default_found = True

                if not new_default_found:
                    self.db_session.rollback()  # Revertir si no se puede asegurar un default
                    error_msg = f"No se pudo eliminar el agente predeterminado '{agent.agent_name}' (ID: {agent_id}) porque no hay otro agente activo para asignar como predeterminado."
                    logger.error(error_msg)
                    raise ValueError(error_msg)

            return self.repo.delete(agent_id)
        except Exception as e:
            logger.error(f"Servicio: Error al eliminar agente de IA {agent_id}: {e}")
            raise  # Re-lanzar
