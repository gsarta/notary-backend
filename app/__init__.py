import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from config import Config
import logging

from app.utils.azure_blob_manager import AzureBlobManager
from app.utils.audio_processor import AudioProcessor
from app.services.transcribe_service import TranscribeService
from app.services.ai_agent_configuration_service import AIAgentConfigurationService
from app.repositories.ai_agent_configuration_repository import (
    AIAgentConfigurationRepository,
)

# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    with app.app_context():
        # Importar modelos para que SQLAlchemy los conozca
        from app.models import roles, users, ai_agent_configuration, transcription

        # from app.models import document_types, template_sections, templates, \
        #                      template_sections_composition, documents, clients, \
        #                      companies, document_client_relations, document_company_relations

        audio_processor = None
        azure_blob_manager = None
        transcribe_service = None

        try:
            # 1. Inicializar AzureBlobManager
            azure_storage_account_name = app.config.get("AZURE_STORAGE_ACCOUNT_NAME")
            azure_storage_account_key = app.config.get("AZURE_STORAGE_ACCOUNT_KEY")
            azure_storage_container_name = app.config.get(
                "AZURE_STORAGE_CONTAINER_NAME"
            )

            if not azure_storage_container_name:
                raise ValueError(
                    "AZURE_STORAGE_CONTAINER_NAME no está configurado en las variables de entorno."
                )

            # Pasa los valores directamente a AzureBlobManager
            azure_blob_manager = AzureBlobManager(
                account_name=azure_storage_account_name,
                account_key=azure_storage_account_key,
                container_name=azure_storage_container_name,
            )
            logger.info("AzureBlobManager inicializado exitosamente.")

            # 2. Inicializar AudioProcessor (puede necesitar credenciales de OpenAI o similares)
            # Asumiendo que AUDIO_PROCESSOR_API_KEY o similar se obtiene de config
            openai_api_key = app.config.get("OPENAI_API_KEY")
            if not openai_api_key:
                raise ValueError(
                    "OPENAI_API_KEY no está configurada en las variables de entorno."
                )

            audio_processor = AudioProcessor(openai_api_key=openai_api_key)
            logger.info("AudioProcessor inicializado exitosamente.")

            # 3. Inicializar TranscribeService
            # Obtener el session maker de SQLAlchemy
            db_session = db.session
            ai_agent_repo = AIAgentConfigurationRepository(db_session)

            # Obtener la duración del segmento de config.py
            segment_duration_ms = app.config.get(
                "SEGMENT_DURATION_MS", 60000
            )  # Default a 60 segundos si no está

            transcribe_service = TranscribeService(
                db_session=db_session,
                audio_processor=audio_processor,
                azure_blob_manager=azure_blob_manager,
                segment_duration_ms=segment_duration_ms,
            )
            logger.info("TranscribeService inicializado exitosamente.")

            app.audio_processor = audio_processor
            app.azure_blob_manager = azure_blob_manager
            app.transcribe_service = transcribe_service

        except Exception as e:
            logger.critical(
                f"Error fatal al inicializar servicios externos: {e}", exc_info=True
            )
            raise RuntimeError(f"Error de inicialización de servicios externos: {e}")

        # Importar y registrar Blueprints (controladores)
        from app.controllers import transcribe_controller
        from app.controllers import ai_agent_configurations_controller

        # TODO: from app.controllers import roles_controller, users_controller # etc.

        app.register_blueprint(transcribe_controller.bp)
        app.register_blueprint(ai_agent_configurations_controller.bp)
        # TODO: app.register_blueprint(roles_controller.bp)
        # TODO: app.register_blueprint(users_controller.bp)

        # Manejador de errores global
        @app.errorhandler(404)
        def not_found_error(error):
            return jsonify({"message": "Recurso no encontrado"}), 404

        @app.errorhandler(500)
        def internal_error(error):
            db.session.rollback()  # Rollback en caso de error 500
            logger.exception("Un error interno del servidor ha ocurrido.")
            return jsonify({"message": "Error interno del servidor"}), 500

    logger.info("Aplicación Flask inicializada exitosamente.")
    return app
