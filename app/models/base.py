from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os

# Base para los modelos declarativos
Base = declarative_base()

# Configuración del motor de la base de datos
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://user:password@host:port/database"
)
engine = create_engine(DATABASE_URL)

# Configuración del Sessionmaker
# autoflush=False: No vacía la sesión automáticamente después de cada operación.
# autocommit=False: Requiere un commit explícito.
# expire_on_commit=False: Los objetos no se "expiran" (invalidan) después de un commit,
#                         lo que puede ser útil para acceder a ellos fuera de la sesión original.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Función para obtener una sesión de base de datos (se usa en los endpoints/servicios)
def get_db():
    db = SessionLocal()
    try:
        yield db  # Esto permite que se use con 'with' o en dependencias de frameworks web (ej. FastAPI/Flask)
    finally:
        db.close()  # Asegura que la sesión se cierre


# Para inicializar la base de datos (crear tablas)
def init_db():
    Base.metadata.create_all(bind=engine)
