import os
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AzureBlobManager:
    def __init__(self, account_name: str, account_key: str, container_name: str):
        """
        Inicializa el cliente de Azure Blob Storage.
        """
        if not account_name or not account_key:
            logger.error(
                "Las credenciales de Azure Blob Storage (nombre de cuenta o clave) no fueron proporcionadas."
            )
            raise ValueError(
                "Las credenciales de Azure Blob Storage no pueden estar vacías."
            )

        self.account_name = account_name
        self.container_name = container_name

        # Construir la cadena de conexión con la clave de cuenta
        connection_string = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"

        try:
            self.blob_service_client = BlobServiceClient.from_connection_string(
                connection_string
            )
            # Asegurarse de que el contenedor exista
            self.container_client = self.blob_service_client.get_container_client(
                container_name
            )
            if not self.container_client.exists():
                logger.info(f"Creando contenedor Azure Blob: {container_name}")
                self.container_client.create_container()
        except Exception as e:
            logger.error(
                f"Error al inicializar AzureBlobManager o crear contenedor '{container_name}': {e}"
            )
            raise RuntimeError(f"Error al conectar con Azure Blob Storage: {e}")

    def upload_blob(self, file_path: str, blob_name: str) -> str:
        """
        Sube un archivo a Azure Blob Storage y retorna su URL pública.
        """
        try:
            blob_client: BlobClient = self.container_client.get_blob_client(blob_name)

            with open(file_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)

            blob_url = blob_client.url
            logger.info(
                f"Archivo '{blob_name}' subido a Azure Blob Storage. URL: {blob_url}"
            )
            return blob_url
        except Exception as e:
            logger.error(
                f"Error al subir el archivo '{file_path}' a Azure Blob como '{blob_name}': {e}"
            )
            raise RuntimeError(f"Error al subir archivo a Azure Blob Storage: {e}")

    def delete_blob(self, blob_name: str):
        """
        Elimina un blob de Azure Blob Storage.
        """
        try:
            blob_client: BlobClient = self.container_client.get_blob_client(blob_name)
            blob_client.delete_blob()
            logger.info(f"Blob '{blob_name}' eliminado de Azure Blob Storage.")
        except Exception as e:
            logger.warning(
                f"Error al eliminar el blob '{blob_name}' de Azure Blob: {e}"
            )
