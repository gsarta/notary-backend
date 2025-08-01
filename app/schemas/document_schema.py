from marshmallow import Schema, fields, validate
import uuid


class DocumentSchema(Schema):
    """
    Esquema para serializar/deserializar objetos Document.
    """

    document_id = fields.UUID(
        dump_only=True,
        required=True,
        metadata={"description": "Identificador único del documento."},
    )
    document_name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=255),
        metadata={"description": "Nombre del documento."},
    )
    document_type_id = fields.UUID(
        required=True, metadata={"description": "ID del tipo de documento asociado."}
    )
    template_id = fields.UUID(
        required=True,
        metadata={
            "description": "ID de la plantilla utilizada para crear el documento."
        },
    )
    text_content = fields.String(
        required=True,
        metadata={"description": "Contenido textual final del documento."},
    )
    pdf_url = fields.String(
        validate=validate.URL(),
        allow_none=True,
        metadata={"description": "URL de descarga del documento en formato PDF."},
    )
    dynamic_data = fields.Raw(
        required=True,
        metadata={
            "description": "Datos dinámicos en formato JSON para rellenar la plantilla."
        },
    )
    created_by = fields.UUID(
        allow_none=True,
        metadata={"description": "ID del usuario que creó el documento."},
    )
    created_at = fields.DateTime(
        dump_only=True,
        metadata={"description": "Fecha y hora de creación del documento."},
    )
    updated_at = fields.DateTime(
        dump_only=True,
        metadata={
            "description": "Fecha y hora de la última actualización del documento."
        },
    )


class DocumentCreateSchema(Schema):
    """
    Esquema para validar los datos al crear un nuevo Documento.
    """

    document_name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=255),
        metadata={"description": "Nombre del documento."},
    )
    document_type_id = fields.UUID(
        required=True, metadata={"description": "ID del tipo de documento asociado."}
    )
    template_id = fields.UUID(
        required=True,
        metadata={
            "description": "ID de la plantilla utilizada para crear el documento."
        },
    )
    dynamic_data = fields.Raw(
        required=True,
        metadata={
            "description": "Datos dinámicos en formato JSON para rellenar la plantilla."
        },
    )
    created_by = fields.UUID(
        allow_none=True,
        metadata={"description": "ID del usuario que creó el documento."},
    )


class DocumentUpdateSchema(Schema):
    """
    Esquema para validar los datos al actualizar un Documento existente.
    Todos los campos son opcionales para permitir actualizaciones parciales.
    """

    document_name = fields.String(
        validate=validate.Length(min=1, max=255),
        metadata={"description": "Nuevo nombre del documento."},
    )
    document_type_id = fields.UUID(
        metadata={"description": "Nuevo ID del tipo de documento asociado."}
    )
    template_id = fields.UUID(
        metadata={"description": "Nuevo ID de la plantilla utilizada."}
    )
    text_content = fields.String(
        metadata={"description": "Nuevo contenido textual final del documento."}
    )
    pdf_url = fields.String(
        validate=validate.URL(),
        allow_none=True,
        metadata={"description": "Nueva URL de descarga del documento en formato PDF."},
    )
    dynamic_data = fields.Raw(
        metadata={"description": "Nuevos datos dinámicos en formato JSON."}
    )
