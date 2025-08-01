from marshmallow import Schema, fields, validate
from marshmallow.fields import UUID as UUIDField


class TemplateSectionCompositionSchema(Schema):
    """Schema para serializar y deserializar objetos TemplateSectionComposition."""

    template_id = UUIDField(required=True)
    section_id = UUIDField(required=True)
    order_index = fields.Integer(
        required=True, validate=validate.Range(min=0)
    )  # El orden debe ser 0 o positivo
    is_mandatory = fields.Boolean(required=False, default=True)
    created_at = fields.DateTime(dump_only=True)


class TemplateSectionCompositionCreateSchema(Schema):
    """Schema para validar la entrada al crear un nuevo TemplateSectionComposition."""

    template_id = UUIDField(required=True)
    section_id = UUIDField(required=True)
    order_index = fields.Integer(required=True, validate=validate.Range(min=0))
    is_mandatory = fields.Boolean(required=False, default=True)


class TemplateSectionCompositionUpdateSchema(Schema):
    """Schema para validar la entrada al actualizar un TemplateSectionComposition.
    Normalmente se identificará la composición por template_id y section_id
    y solo se actualizarán order_index o is_mandatory.
    """

    order_index = fields.Integer(required=False, validate=validate.Range(min=0))
    is_mandatory = fields.Boolean(required=False)
