import uuid
from sqlalchemy.orm import Session
from app.models.roles import Role


class RoleRepository:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_by_id(self, role_id: uuid.UUID) -> Role | None:
        """Obtiene un rol por su ID."""
        return self.db_session.query(Role).filter_by(role_id=role_id).first()

    def get_by_name(self, role_name: str) -> Role | None:
        """Obtiene un rol por su nombre."""
        return self.db_session.query(Role).filter_by(role_name=role_name).first()

    def get_all(self) -> list[Role]:
        """Obtiene todos los roles."""
        return self.db_session.query(Role).all()

    def create(self, role: Role) -> Role:
        """Crea un nuevo rol en la base de datos."""
        self.db_session.add(role)
        self.db_session.commit()
        self.db_session.refresh(role)
        return role

    def update(self, role_id: uuid.UUID, update_data: dict) -> Role | None:
        """Actualiza un rol existente por su ID."""
        role = self.get_by_id(role_id)
        if role:
            for key, value in update_data.items():
                if hasattr(role, key):
                    setattr(role, key, value)
            self.db_session.commit()
            self.db_session.refresh(role)
        return role

    def delete(self, role_id: uuid.UUID) -> bool:
        """Elimina un rol por su ID."""
        role = self.get_by_id(role_id)
        if role:
            self.db_session.delete(role)
            self.db_session.commit()
            return True
        return False
