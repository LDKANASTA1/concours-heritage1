"""
Configuration centrale de l'application.
Toutes les valeurs sont lues depuis le fichier .env (voir .env.example).
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Base de données
    DATABASE_URL: str = "sqlite:///./heritage1.db"

    # ImgBB
    IMGBB_API_KEY: str = ""

    # JWT
    SECRET_KEY: str = "changez-moi"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 jours

    # Support
    SUPPORT_EMAIL: str = "ldkanasta@gmail.com"
    SUPPORT_PHONE: str = "+243826740490"
    SUPPORT_WHATSAPP_URL: str = "https://wa.me/243826740490"

    # SMTP
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "ldkanasta@gmail.com"
    SMTP_ENABLED: bool = True

    # URLs
    BASE_URL: str = "https://concours-backend-686g.onrender.com"
    FRONTEND_URL: str = "https://ldkanasta1.github.io/concours-heritage1/"

    # Environnement
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # École
    NOM_ECOLE: str = "Complexe Scolaire HERITAGE 1"
    PAYS: str = "République Démocratique du Congo"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()

# Liste des options disponibles au Complexe Scolaire HERITAGE 1
OPTIONS_DISPONIBLES = [
    {"code": "MG", "nom": "Mécanique générale"},
    {"code": "ELEC", "nom": "Électricité générale"},
    {"code": "MET", "nom": "Métallurgie"},
    {"code": "TCC", "nom": "Coupe et couture"},
    {"code": "HP", "nom": "Pédagogie générale"},
    {"code": "SC", "nom": "Scientifiques"},
    {"code": "CG", "nom": "Commercial de gestion"},
]

OPTIONS_CODES = [o["code"] for o in OPTIONS_DISPONIBLES]
