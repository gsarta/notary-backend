import os
from typing import Dict
import logging

from keycloak import KeycloakAdmin

logger = logging.getLogger(__name__)

def get_keycloak_admin():
    keycloak_config = {
        "server_url": os.getenv("KEYCLOAK_URL"),
        "username": os.getenv("KEYCLOAK_ADMIN_USERNAME"),
        "password": os.getenv("KEYCLOAK_ADMIN_PASSWORD"),
        "realm_name": os.getenv("OIDC_REALM"),
        "client_id": os.getenv("OIDC_CLIENT_ID"),
        "client_secret_key": os.getenv("OIDC_CLIENT_SECRET")
    }

    return KeycloakAdmin(
        server_url=keycloak_config["server_url"],
        username=keycloak_config["username"],
        password=keycloak_config["password"],
        realm_name=keycloak_config["realm_name"],
        client_id=keycloak_config["client_id"],
        client_secret_key=keycloak_config["client_secret_key"],
        verify=True
    )

def create_user_in_keycloak(*, user_data: Dict):
    try:
        keycloak_user_data = {
            "username": user_data["email"],
            "email": user_data["email"],
            "firstName": user_data["first_name"],
            "lastName": user_data["last_name"],
            "enabled": True,
            "credentials": [{
                "type": "password",
                "value": user_data["password"],
                "temporary": False
            }]
        }

        keycloak_admin = get_keycloak_admin()
        keycloak_user_id = keycloak_admin.create_user(keycloak_user_data)
        logger.info(f"[Keycloak Service] User created successfully in Keycloak with oauth_id='{keycloak_user_id}'")
        return keycloak_user_id
    except Exception as e:
        logger.error(f"[Keycloak Service] An error occurred while creating the user in Keycloak: {str(e)}")
        raise ValueError(e)

def validate_user_email_in_keycloak(*, email: str):
    keycloak_admin = get_keycloak_admin()
    users = keycloak_admin.get_users({ "email": email })
    if users:
        raise ValueError("An User with this email already exists in Keycloak.")

def delete_user_in_keycloak_by_oauth_id(*, oauth_id: str):
    try:
        keycloak_admin = get_keycloak_admin()
        keycloak_admin.delete_user(oauth_id)
        logger.info(f"[Keycloak Service] User with oauth_id '{oauth_id}' successfully deleted in Keycloak")
    except Exception as e:
        logger.error(f"[Keycloak Service] An error occurred while deleting the user in Keycloak: {str(e)}")
        raise e
