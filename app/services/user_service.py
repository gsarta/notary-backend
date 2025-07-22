import uuid
from sqlalchemy.orm import Session
from app.repositories.user_repository import UserRepository
from app.repositories.role_repository import RoleRepository
from app.models.users import User
import logging

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, db_session: Session):
        self.user_repo = UserRepository(db_session)
        self.role_repo = RoleRepository(db_session)
        self.db_session = db_session

    def get_all_users(self) -> list[User]:
        """Obtiene todos los usuarios disponibles."""
        return self.user_repo.get_all()

    def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        """Obtiene un usuario específico por su ID."""
        return self.user_repo.get_by_id(user_id)

    def get_user_by_username(self, username: str) -> User | None:
        """Obtiene un usuario por su nombre de usuario."""
        return self.user_repo.get_by_username(username)

    def get_user_by_email(self, email: str) -> User | None:
        """Obtiene un usuario por su correo electrónico."""
        return self.user_repo.get_by_email(email)

    def create_user(
        self,
        username: str,
        email: str,
        role_id: uuid.UUID,
        first_name: str = None,
        last_name: str = None,
        is_active: bool = True,
    ) -> User:
        """
        Crea un nuevo usuario.
        Valida que el nombre de usuario y el email no existan y que el role_id sea válido.
        """
        if self.user_repo.get_by_username(username):
            raise ValueError(f"El nombre de usuario '{username}' ya está en uso.")
        if self.user_repo.get_by_email(email):
            raise ValueError(f"El correo electrónico '{email}' ya está registrado.")

        # Validar que el role_id exista
        if not self.role_repo.get_by_id(role_id):
            raise ValueError(f"El role_id '{role_id}' no es válido.")

        new_user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_active=is_active,
            role_id=role_id,
        )
        try:
            return self.user_repo.create(new_user)
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error al crear usuario '{username}': {e}", exc_info=True)
            raise RuntimeError("Error al guardar el usuario en la base de datos.")

    def update_user(
        self,
        user_id: uuid.UUID,
        username: str = None,
        email: str = None,
        role_id: uuid.UUID = None,
        first_name: str = None,
        last_name: str = None,
        is_active: bool = None,
    ) -> User | None:
        """Actualiza la información de un usuario existente."""
        update_data = {}
        if username is not None:
            existing_user_with_username = self.user_repo.get_by_username(username)
            if (
                existing_user_with_username
                and existing_user_with_username.user_id != user_id
            ):
                raise ValueError(
                    f"El nombre de usuario '{username}' ya está en uso por otro usuario."
                )
            update_data["username"] = username

        if email is not None:
            existing_user_with_email = self.user_repo.get_by_email(email)
            if existing_user_with_email and existing_user_with_email.user_id != user_id:
                raise ValueError(
                    f"El correo electrónico '{email}' ya está registrado por otro usuario."
                )
            update_data["email"] = email

        if role_id is not None:
            if not self.role_repo.get_by_id(role_id):
                raise ValueError(f"El role_id '{role_id}' no es válido.")
            update_data["role_id"] = role_id

        if first_name is not None:
            update_data["first_name"] = first_name
        if last_name is not None:
            update_data["last_name"] = last_name
        if is_active is not None:
            update_data["is_active"] = is_active

        if not update_data:
            raise ValueError("No se proporcionaron datos para actualizar el usuario.")

        try:
            updated_user = self.user_repo.update(user_id, update_data)
            if not updated_user:
                raise ValueError(f"Usuario con ID '{user_id}' no encontrado.")
            return updated_user
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error al actualizar usuario '{user_id}': {e}", exc_info=True)
            raise RuntimeError("Error al actualizar el usuario en la base de datos.")

    def delete_user(self, user_id: uuid.UUID) -> bool:
        """Elimina un usuario por su ID."""
        # TODO: Considerar lógica para evitar eliminar usuarios si tienen datos asociados críticos (ej. transcripciones).
        try:
            deleted = self.user_repo.delete(user_id)
            if not deleted:
                raise ValueError(
                    f"Usuario con ID '{user_id}' no encontrado o no se pudo eliminar."
                )
            return deleted
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error al eliminar usuario '{user_id}': {e}", exc_info=True)
            raise RuntimeError("Error al eliminar el usuario de la base de datos.")
