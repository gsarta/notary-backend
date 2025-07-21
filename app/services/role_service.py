import uuid
from sqlalchemy.orm import Session
from app.repositories.role_repository import RoleRepository
from app.models.roles import Role
import logging

logger = logging.getLogger(__name__)


class RoleService:
    def __init__(self, db_session: Session):
        self.role_repo = RoleRepository(db_session)
        self.db_session = db_session

    def get_all_roles(self) -> list[Role]:
        """Obtiene todos los roles disponibles."""
        return self.role_repo.get_all()

    def get_role_by_id(self, role_id: uuid.UUID) -> Role | None:
        """Obtiene un rol específico por su ID."""
        return self.role_repo.get_by_id(role_id)

    def create_role(self, role_name: str, description: str = None) -> Role:
        """Crea un nuevo rol. Valida que el nombre del rol no exista."""
        if self.role_repo.get_by_name(role_name):
            raise ValueError(f"El rol con nombre '{role_name}' ya existe.")

        new_role = Role(role_name=role_name, description=description)
        try:
            return self.role_repo.create(new_role)
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error al crear rol '{role_name}': {e}", exc_info=True)
            raise RuntimeError("Error al guardar el rol en la base de datos.")

    def update_role(
        self, role_id: uuid.UUID, role_name: str = None, description: str = None
    ) -> Role | None:
        """Actualiza la información de un rol existente."""
        update_data = {}
        if role_name is not None:
            # Si se intenta cambiar el nombre, verificar que el nuevo nombre no exista para otro rol
            existing_role_with_name = self.role_repo.get_by_name(role_name)
            if existing_role_with_name and existing_role_with_name.role_id != role_id:
                raise ValueError(
                    f"El rol con nombre '{role_name}' ya existe para otro ID."
                )
            update_data["role_name"] = role_name
        if description is not None:
            update_data["description"] = description

        if not update_data:
            raise ValueError("No se proporcionaron datos para actualizar el rol.")

        try:
            updated_role = self.role_repo.update(role_id, update_data)
            if not updated_role:
                raise ValueError(f"Rol con ID '{role_id}' no encontrado.")
            return updated_role
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error al actualizar rol '{role_id}': {e}", exc_info=True)
            raise RuntimeError("Error al actualizar el rol en la base de datos.")

    def delete_role(self, role_id: uuid.UUID) -> bool:
        """Elimina un rol por su ID."""
        # TODO: Considerar lógica para evitar eliminar roles que estén asignados a usuarios.
        # Por ahora, simplemente intenta eliminar.
        try:
            deleted = self.role_repo.delete(role_id)
            if not deleted:
                raise ValueError(
                    f"Rol con ID '{role_id}' no encontrado o no se pudo eliminar."
                )
            return deleted
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error al eliminar rol '{role_id}': {e}", exc_info=True)
            raise RuntimeError("Error al eliminar el rol de la base de datos.")
