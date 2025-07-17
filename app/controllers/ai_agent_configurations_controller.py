from flask import Blueprint, request, jsonify, g
from app.services.ai_agent_configuration_service import AIAgentConfigurationService
from app.schemas.ai_agent_configuration_schema import AIAgentConfigurationSchema
from app import db
import uuid
import logging

bp = Blueprint("ai_agents", __name__, url_prefix="/api/ai_agents")
ai_agent_schema = AIAgentConfigurationSchema()
ai_agents_schema = AIAgentConfigurationSchema(many=True)

logger = logging.getLogger(__name__)


# Middleware para inyectar el servicio en el contexto de la solicitud
@bp.before_request
def before_request():
    g.ai_agent_service = AIAgentConfigurationService(db.session)


@bp.route("/", methods=["GET"])
def get_ai_agents():
    """Obtiene una lista de todas las configuraciones de agentes de IA."""
    try:
        agents = g.ai_agent_service.get_all_agents()
        return jsonify(ai_agents_schema.dump(agents)), 200
    except Exception as e:
        logger.exception("Error al obtener agentes de IA.")
        return (
            jsonify(
                {"message": "Error interno del servidor al obtener agentes de IA."}
            ),
            500,
        )


@bp.route("/<uuid:agent_id>", methods=["GET"])
def get_ai_agent(agent_id: uuid.UUID):
    """Obtiene una configuración de agente de IA por su ID."""
    try:
        agent = g.ai_agent_service.get_agent_by_id(agent_id)
        if agent:
            return jsonify(ai_agent_schema.dump(agent)), 200
        return jsonify({"message": "Agente de IA no encontrado."}), 404
    except Exception as e:
        logger.exception(f"Error al obtener agente de IA con ID {agent_id}.")
        return (
            jsonify({"message": "Error interno del servidor al obtener agente de IA."}),
            500,
        )


@bp.route("/", methods=["POST"])
def create_ai_agent():
    """Crea una nueva configuración de agente de IA."""
    try:
        # Validar la entrada con el esquema
        agent_data = ai_agent_schema.load(request.json)

        new_agent = g.ai_agent_service.create_agent(agent_data)
        return jsonify(ai_agent_schema.dump(new_agent)), 201
    except Exception as e:
        logger.exception("Error al crear agente de IA.")
        # Marshmallow levanta ValidationError si la validación falla
        if hasattr(e, "messages"):  # Si es un ValidationError de Marshmallow
            return (
                jsonify({"message": "Error de validación", "errors": e.messages}),
                400,
            )
        return (
            jsonify(
                {"message": f"Error interno del servidor al crear agente de IA: {e}"}
            ),
            500,
        )


@bp.route("/<uuid:agent_id>", methods=["PUT", "PATCH"])
def update_ai_agent(agent_id: uuid.UUID):
    """Actualiza una configuración de agente de IA existente."""
    try:
        # Usar partial=True para permitir actualizaciones parciales (PATCH)
        update_data = ai_agent_schema.load(request.json, partial=True)

        updated_agent = g.ai_agent_service.update_agent(agent_id, update_data)
        if updated_agent:
            return jsonify(ai_agent_schema.dump(updated_agent)), 200
        return jsonify({"message": "Agente de IA no encontrado."}), 404
    except Exception as e:
        logger.exception(f"Error al actualizar agente de IA con ID {agent_id}.")
        if hasattr(e, "messages"):
            return (
                jsonify({"message": "Error de validación", "errors": e.messages}),
                400,
            )
        return (
            jsonify(
                {
                    "message": f"Error interno del servidor al actualizar agente de IA: {e}"
                }
            ),
            500,
        )


@bp.route("/<uuid:agent_id>", methods=["DELETE"])
def delete_ai_agent(agent_id: uuid.UUID):
    """Elimina una configuración de agente de IA."""
    try:
        if g.ai_agent_service.delete_agent(agent_id):
            return jsonify({"message": "Agente de IA eliminado exitosamente."}), 204
        return jsonify({"message": "Agente de IA no encontrado."}), 404
    except Exception as e:
        logger.exception(f"Error al eliminar agente de IA con ID {agent_id}.")
        return (
            jsonify(
                {"message": f"Error interno del servidor al eliminar agente de IA: {e}"}
            ),
            500,
        )
