import os
import uuid

from flask import Flask, redirect, url_for, session, g, jsonify, request
from flask_sqlalchemy import SQLAlchemy

from app.config.keycloak_config import get_keycloak_openid
from config import Config
import logging
from app.utils.azure_blob_manager import AzureBlobManager
from app.utils.audio_processor import AudioProcessor
from app.services.transcribe_service import TranscribeService
from app.services.ai_agent_configuration_service import AIAgentConfigurationService
from app.repositories.ai_agent_configuration_repository import (
    AIAgentConfigurationRepository,
)
from app.models.document_type import DocumentType

app = Flask(__name__)
# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
keycloak_openid = get_keycloak_openid()


@app.route("/login")
def login():
    auth_url = keycloak_openid.auth_url(
        redirect_uri="http://localhost:8000/oidc_callback"
    )
    return redirect(auth_url)


@app.route("/oidc_callback")
def callback():
    code = request.args.get("code")
    if code:
        token = keycloak_openid.token(
            grant_type="authorization_code",
            code=code,
            redirect_uri="http://localhost:8000/oidc_callback",
        )
        session["access_token"] = token["access_token"]
        session["refresh_token"] = token["refresh_token"]

        next_url = session.pop("next_url", None)
        if next_url:
            return redirect(next_url)
    return "Authorization failed", 400


def create_app():
    app.config.from_object(Config)
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY")
    if not app.config["SECRET_KEY"]:
        logging.error(
            "FLASK_SECRET_KEY no está configurada. ¡Esto es INSEGURO para producción!"
        )
        app.config["SECRET_KEY"] = "fallback_secret_key_for_dev_only"

    db = SQLAlchemy()

    db.init_app(app)
    app.db = db

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
        from app.controllers import roles_controller
        from app.controllers import users_controller
        from app.controllers import template_controller
        from app.controllers import template_section_composition_controller
        from app.controllers import template_section_controller
        from app.controllers import document_types_controller
        from app.controllers import document_controller

        # TODO: from app.controllers import roles_controller, users_controller # etc.

        app.register_blueprint(transcribe_controller.bp)
        app.register_blueprint(ai_agent_configurations_controller.bp)
        app.register_blueprint(roles_controller.bp)
        app.register_blueprint(users_controller.bp)
        app.register_blueprint(template_controller.bp)
        app.register_blueprint(template_section_composition_controller.bp)
        app.register_blueprint(template_section_controller.bp)
        app.register_blueprint(document_types_controller.bp)
        app.register_blueprint(document_controller.bp)

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
