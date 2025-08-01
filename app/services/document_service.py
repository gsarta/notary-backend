from sqlalchemy.orm import Session
from uuid import UUID
import logging
import json

from app.repositories.document_repository import DocumentRepository
from app.schemas.document_schema import (
    DocumentSchema,
    DocumentCreateSchema,
    DocumentUpdateSchema,
)
from app.services.template_service import TemplateService
from app.services.template_section_composition_service import (
    TemplateSectionCompositionService,
)
from app.services.template_section_service import TemplateSectionService


logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(
        self,
        db_session: Session,
        template_service: TemplateService,
        template_section_composition_service: TemplateSectionCompositionService,
        template_section_service: TemplateSectionService,
    ):
        self.repository = DocumentRepository(db_session)
        self.schema = DocumentSchema()
        self.create_schema = DocumentCreateSchema()
        self.update_schema = DocumentUpdateSchema()
        self.template_service = template_service
        self.template_section_composition_service = template_section_composition_service
        self.template_section_service = template_section_service

    def get_all_documents(self) -> list[dict]:
        """Obtiene todos los documentos."""
        documents = self.repository.get_all()
        return [self.schema.dump(d) for d in documents]

    def get_document_by_id(self, document_id: UUID) -> dict | None:
        """Obtiene un documento por su ID."""
        document = self.repository.get_by_id(document_id)
        if not document:
            return None
        return self.schema.dump(document)

    def create_document(self, document_data: dict) -> dict:
        """
        Crea un nuevo documento, fusionando la plantilla, las secciones y los datos dinámicos.
        Args:
            document_data (dict): Datos para crear el documento, incluyendo template_id y dynamic_data.
                                  Ejemplo: {
                                      "document_name": "Contrato de Prueba",
                                      "document_type_id": "uuid_del_tipo_de_documento",
                                      "template_id": "uuid_de_la_plantilla",
                                      "dynamic_data": {"nombre_cliente": "Juan Perez", "fecha": "2024-07-29"}
                                  }
        Returns:
            dict: El documento recién creado serializado.
        Raises:
            ValueError: Si los datos de entrada son inválidos o faltan plantillas/secciones.
            RuntimeError: Si ocurre un error durante la generación del contenido o la persistencia.
        """
        errors = self.create_schema.validate(document_data)
        if errors:
            logger.error(f"Errores de validación al crear documento: {errors}")
            raise ValueError(f"Datos de entrada inválidos: {errors}")

        template_id = document_data["template_id"]
        dynamic_data = document_data.get("dynamic_data", {})

        # 1. Obtener la plantilla base
        template = self.template_service.get_template_by_id(template_id)
        if not template:
            raise ValueError(f"Plantilla con ID '{template_id}' no encontrada.")

        combined_text_content = template.get("base_content", "")

        # 2. Obtener las composiciones de secciones para la plantilla
        section_compositions = (
            self.template_section_composition_service.get_compositions_by_template_id(
                template_id
            )
        )

        # Ordenar las secciones por su order_index
        sorted_compositions = sorted(
            section_compositions, key=lambda x: x.get("order_index", 0)
        )

        # 3. Construir el contenido textual combinando plantilla base y secciones
        for composition_data in sorted_compositions:
            section_id = composition_data.get("template_section_id")
            if section_id:
                section = self.template_section_service.get_template_section_by_id(
                    section_id
                )
                if section:
                    # Añade un salto de línea entre secciones si no es la primera sección
                    if combined_text_content:
                        combined_text_content += "\n"
                    combined_text_content += section.get("content", "")

        # 4. Sustituir variables dinámicas en el contenido combinado
        final_text_content = self._replace_placeholders(
            combined_text_content, dynamic_data
        )

        # 5. TODO: Placeholder para generación de PDF y URL
        # Esta parte es compleja e implica:
        # a) Renderizar final_text_content a HTML/Markdown.
        # b) Usar una librería como WeasyPrint (para HTML a PDF) o ReportLab (para PDF programático).
        # c) Subir el PDF generado a Azure Blob Storage.
        # Por ahora, simplemente estableceremos pdf_url a None. Esto se puede expandir más adelante.
        pdf_url = None  # Lógica de generación y subida de PDF aquí

        # Preparar los datos finales para el repositorio
        document_for_repo = {
            "document_name": document_data["document_name"],
            "document_type_id": document_data["document_type_id"],
            "template_id": template_id,
            "text_content": final_text_content,
            "pdf_url": pdf_url,
            "dynamic_data": dynamic_data,  # Almacenar los datos dinámicos tal como se recibieron
            "created_by": document_data.get("created_by"),
        }

        # 6. Crear el documento en la base de datos
        new_document_orm = self.repository.create(document_for_repo)
        return self.schema.dump(new_document_orm)

    def update_document(self, document_id: UUID, update_data: dict) -> dict | None:
        """
        Actualiza un documento existente.
        Considera que si se actualizan template_id o dynamic_data,
        podría ser necesaria una re-generación del text_content y pdf_url.
        Por simplicidad inicial, si se modifica `text_content` directamente, se usa ese valor.
        Si se actualiza `dynamic_data` sin `text_content`, se debería re-generar.
        """
        errors = self.update_schema.validate(update_data)
        if errors:
            logger.error(
                f"Errores de validación al actualizar documento (ID: {document_id}): {errors}"
            )
            raise ValueError(f"Datos de entrada inválidos: {errors}")

        document_orm = self.repository.get_by_id(document_id)
        if not document_orm:
            return None

        # Lógica para re-generar text_content si cambian dynamic_data o template_id
        # Esto es más complejo y lo podemos desarrollar en detalle si es requerido.
        # Por ahora, si 'text_content' se proporciona en update_data, se usa ese valor.
        # Si 'dynamic_data' se actualiza sin 'text_content', y queremos re-generar:
        if "dynamic_data" in update_data and "text_content" not in update_data:
            # Obtener la plantilla y composiciones para re-generar
            template = self.template_service.get_template_by_id(
                document_orm.template_id
            )
            if template:
                combined_content = template.get("base_content", "")
                section_compositions = self.template_section_composition_service.get_compositions_by_template_id(
                    document_orm.template_id
                )
                sorted_compositions = sorted(
                    section_compositions, key=lambda x: x.get("order_index", 0)
                )
                for composition_data in sorted_compositions:
                    section_id = composition_data.get("template_section_id")
                    if section_id:
                        section = (
                            self.template_section_service.get_template_section_by_id(
                                section_id
                            )
                        )
                        if section:
                            if combined_content:
                                combined_content += "\n"
                            combined_content += section.get("content", "")

                # Usar los nuevos dynamic_data para la sustitución
                new_dynamic_data = update_data["dynamic_data"]
                updated_text_content = self._replace_placeholders(
                    combined_content, new_dynamic_data
                )
                update_data["text_content"] = updated_text_content
                # También podrías generar un nuevo PDF aquí si la lógica está lista
                # update_data["pdf_url"] = new_pdf_url

        updated_document_orm = self.repository.update(document_orm, update_data)
        return self.schema.dump(updated_document_orm)

    def delete_document(self, document_id: UUID) -> bool:
        """Elimina un documento por su ID."""
        document = self.repository.get_by_id(document_id)
        if not document:
            return False
        self.repository.delete(document)
        return True

    def _replace_placeholders(self, content: str, data: dict) -> str:
        """
        Reemplaza los placeholders en el contenido con los datos proporcionados.
        Formato de placeholder: {{variable_name}}
        """
        # Asegúrate de que los valores sean cadenas para la sustitución
        sanitized_data = {str(k): str(v) for k, v in data.items()}

        # Realiza la sustitución de forma segura y eficiente
        import re

        def replace_match(match):
            key = match.group(1)
            return sanitized_data.get(
                key, match.group(0)
            )  # Si la clave no existe, deja el placeholder original

        return re.sub(r"\{\{([^}]+)\}\}", replace_match, content)
