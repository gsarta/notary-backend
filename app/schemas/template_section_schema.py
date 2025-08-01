from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class TemplateSectionBase(BaseModel):
    """Base schema for template sections, common fields."""

    section_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Unique name for the template section.",
    )
    html_content: str = Field(
        ..., min_length=1, description="HTML content of the template section."
    )
    variables_schema: Optional[dict] = Field(
        None, description="JSON schema defining variables used in html_content."
    )
    description: Optional[str] = Field(
        None, description="Optional description for the template section."
    )


class TemplateSectionCreate(TemplateSectionBase):
    """Schema for creating a new template section."""

    pass


class TemplateSectionUpdate(BaseModel):
    """Schema for updating an existing template section."""

    section_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="New name for the template section.",
    )
    html_content: Optional[str] = Field(
        None, min_length=1, description="New HTML content of the template section."
    )
    variables_schema: Optional[dict] = Field(
        None, description="New JSON schema defining variables."
    )
    description: Optional[str] = Field(
        None, description="New description for the template section."
    )


class TemplateSectionResponse(TemplateSectionBase):
    """Schema for responding with a template section."""

    section_id: UUID = Field(
        ..., description="Unique identifier of the template section."
    )
    created_at: datetime = Field(
        ..., description="Timestamp when the template section was created."
    )
    updated_at: datetime = Field(
        ..., description="Timestamp when the template section was last updated."
    )

    class Config:
        from_attributes = True  # Allows Pydantic to read ORM models
        json_schema_extra = {
            "example": {
                "section_id": "123e4567-e89b-12d3-a456-426614174000",
                "section_name": "Sección de Cláusula de Precio",
                "html_content": "<p>El precio de venta es {{ price }} {{ currency }}.</p>",
                "variables_schema": {
                    "type": "object",
                    "properties": {
                        "price": {"type": "number"},
                        "currency": {"type": "string"},
                    },
                    "required": ["price", "currency"],
                },
                "description": "Sección para especificar el precio de un bien.",
                "created_at": "2025-07-28T10:00:00Z",
                "updated_at": "2025-07-28T10:30:00Z",
            }
        }
