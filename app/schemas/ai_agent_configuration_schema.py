from marshmallow import Schema, fields, validate, post_load
import uuid


class AIAgentConfigurationSchema(Schema):
    agent_id = fields.UUID(dump_only=True)
    agent_name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    provider = fields.String(
        required=True, validate=validate.OneOf(["OPENAI", "AWS_BEDROCK", "GOOGLE_AI"])
    )
    model_name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    api_base_url = fields.URL()  # Opcional
    api_key_secret_name = fields.String(
        validate=validate.Length(max=100)
    )  # Nombre del secreto en el entorno
    config_json = fields.Raw(
        missing={}
    )  # Para manejar JSONB, podría ser fields.Dict() también, default a diccionario vacío
    is_active = fields.Boolean(missing=True)  # Valor por defecto al crear
    is_default = fields.Boolean(missing=False)  # Valor por defecto al crear
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    @post_load
    def make_ai_agent_configuration(self, data, **kwargs):
        # Asegurarse de que is_default sea un booleano explícito si viene nulo
        if "is_default" in data and data["is_default"] is None:
            data["is_default"] = False
        return data
