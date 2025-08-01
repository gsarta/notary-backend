from marshmallow import Schema, fields, validate
from marshmallow.fields import UUID as UUIDField


class TemplateSchema(Schema):
    template_id = UUIDField(dump_only=True)
    template_name = fields.String(
        required=True, validate=validate.Length(min=1, max=255)
    )
    description = fields.String(required=True)
    document_type_id = UUIDField(required=False, allow_none=True)
    is_active = fields.Boolean(missing=True)
    created_by = UUIDField(required=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class TemplateCreateSchema(Schema):
    """Schema para validar la entrada al crear un nuevo Template."""

    template_name = fields.String(
        required=True, validate=validate.Length(min=1, max=255)
    )
    description = fields.String(allow_none=True)
    document_type_id = UUIDField(allow_none=True)
    is_active = fields.Boolean(required=False, default=True)
    created_by = UUIDField(required=True)


class TemplateUpdateSchema(Schema):
    """Schema para validar la entrada al actualizar un Template existente."""

    template_name = fields.String(validate=validate.Length(min=1, max=255))
    description = fields.String()
    template_type = fields.String(validate=validate.Length(min=1, max=50))
    document_type_id = UUIDField(allow_none=True)
    is_active = fields.Boolean()
    updated_at = fields.DateTime(dump_only=True)
