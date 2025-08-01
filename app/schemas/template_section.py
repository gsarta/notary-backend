from marshmallow import Schema, fields, validate
from marshmallow.fields import (
    UUID as UUIDField,
)


class TemplateSectionSchema(Schema):
    """Schema para serializar y deserializar objetos TemplateSection."""

    section_id = UUIDField(dump_only=True)
    section_name = fields.String(
        required=True, validate=validate.Length(min=1, max=255)
    )
    section_content_template = fields.String(
        required=True, validate=validate.Length(min=1)
    )
    variables_schema = fields.Raw(
        required=True, default={}
    )  # Usamos fields.Raw para el campo JSONB
    description = fields.String(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class TemplateSectionCreateSchema(Schema):
    """Schema para validar la entrada al crear un nuevo TemplateSection."""

    section_name = fields.String(
        required=True, validate=validate.Length(min=1, max=255)
    )
    section_content_template = fields.String(
        required=True, validate=validate.Length(min=1)
    )
    variables_schema = fields.Raw(required=False, default={})
    description = fields.String(allow_none=True)


class TemplateSectionUpdateSchema(Schema):
    """Schema para validar la entrada al actualizar un TemplateSection existente."""

    section_name = fields.String(
        required=False, validate=validate.Length(min=1, max=255)
    )
    section_content_template = fields.String(
        required=False, validate=validate.Length(min=1)
    )
    variables_schema = fields.Raw(required=False)
    description = fields.String(allow_none=True)
