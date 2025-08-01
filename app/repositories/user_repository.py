import uuid
from sqlalchemy.orm import Session
from app.models.users import User


class UserRepository:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Obtiene un usuario por su ID."""
        return self.db_session.query(User).filter_by(user_id=user_id, is_active=True).first()

    def get_by_username(self, username: str) -> User | None:
        """Obtiene un usuario por su nombre de usuario."""
        return self.db_session.query(User).filter_by(username=username, is_active=True).first()

    def get_by_email(self, email: str) -> User | None:
        """Obtiene un usuario por su correo electrónico."""
        return self.db_session.query(User).filter_by(email=email, is_active=True).first()

    def get_all(self) -> list[User]:
        """Obtiene todos los usuarios."""
        return self.db_session.query(User).filter_by(is_active=True).all()

    def create(self, user: User) -> User:
        """Crea un nuevo usuario en la base de datos."""
        self.db_session.add(user)
        self.db_session.commit()
        self.db_session.refresh(user)
        return user

    def update(self, user_id: uuid.UUID, update_data: dict) -> User | None:
        """Actualiza un usuario existente por su ID."""
        user = self.get_by_id(user_id)
        if user:
            for key, value in update_data.items():
                if hasattr(user, key) and key not in [
                    "user_id",
                    "created_at",
                    "updated_at",
                ]:  # No permitir actualización de PK o timestamps automáticos
                    setattr(user, key, value)
            self.db_session.commit()
            self.db_session.refresh(user)
        return user

    def delete(self, user_id: uuid.UUID) -> bool:
        """Elimina un usuario por su ID."""
        user = self.get_by_id(user_id)
        if user:
            self.db_session.delete(user)
            self.db_session.commit()
            return True
        return False
