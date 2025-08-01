from marshmallow import Schema, fields, validate


class DocumentTypeSchema(Schema):
    """Schema para serializar y deserializar objetos DocumentType."""

    document_type_id = fields.UUID(dump_only=True)
    type_name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    description = fields.String(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class DocumentTypeCreateSchema(Schema):
    """Schema para validar la entrada al crear un nuevo DocumentType."""

    type_name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    description = fields.String(allow_none=True)


class DocumentTypeUpdateSchema(Schema):
    """Schema para validar la entrada al actualizar un DocumentType existente."""

    type_name = fields.String(required=False, validate=validate.Length(min=1, max=100))
    description = fields.String(allow_none=True)
