import os

import keycloak

def get_keycloak_openid():
    return keycloak.KeycloakOpenID(
        server_url='http://localhost:8080/',
        client_id='notary-backend-client',
        realm_name='master',
        client_secret_key='ElU6DBkcuy3Q6jqotTzNRQPakuonBco3'
    )
