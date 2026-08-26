"""
Connexion à la base de données.
Fonctionne aussi bien avec SQLite (développement) qu'avec PostgreSQL (production) :
la seule chose à changer est la variable DATABASE_URL dans le fichier .env.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

# SQLite a besoin d'une option supplémentaire pour fonctionner avec FastAPI (multi-thread)
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dépendance FastAPI : fournit une session DB et la ferme proprement après la requête."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
