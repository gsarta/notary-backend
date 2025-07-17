from marshmallow import Schema, fields
import uuid


class TranscriptionSchema(Schema):
    transcription_id = fields.UUID(required=True)
    audio_url = fields.String(required=True)
    text_content = fields.String(required=True)
    duration_seconds = fields.Integer()
    status = fields.String(required=True)
    agent_id = fields.UUID()
    created_by = fields.UUID()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
