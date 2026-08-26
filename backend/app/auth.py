"""Authentification : hashing des PIN avec bcrypt, création/validation des jetons JWT."""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Administrateur, IdentifiantConnexion, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/connexion", auto_error=False)
oauth2_scheme_admin = OAuth2PasswordBearer(tokenUrl="api/admin/connexion", auto_error=False)

MAX_TENTATIVES = 3
DUREE_VERROUILLAGE_MINUTES = 15


def hasher_pin(pin: str) -> str:
    return pwd_context.hash(pin)


def verifier_pin(pin: str, pin_hash: str) -> bool:
    return pwd_context.verify(pin, pin_hash)


def creer_token_acces(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decoder_token(token: str) -> Optional[int]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return int(payload.get("sub"))
    except (JWTError, ValueError, TypeError):
        return None


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    exception_auth = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Session invalide ou expirée. Veuillez vous reconnecter.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise exception_auth
    user_id = decoder_token(token)
    if user_id is None:
        raise exception_auth
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.est_actif:
        raise exception_auth
    return user


def creer_token_admin(admin_id: int) -> str:
    expire = datetime.utcnow() + timedelta(hours=12)
    payload = {"sub": f"admin:{admin_id}", "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def get_current_admin(token: str = Depends(oauth2_scheme_admin), db: Session = Depends(get_db)) -> Administrateur:
    exception_auth = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Session administrateur invalide ou expirée.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise exception_auth
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        sub = payload.get("sub", "")
        if not sub.startswith("admin:"):
            raise exception_auth
        admin_id = int(sub.split(":")[1])
    except (JWTError, ValueError, IndexError):
        raise exception_auth
    admin = db.query(Administrateur).filter(Administrateur.id == admin_id).first()
    if admin is None or not admin.est_actif:
        raise exception_auth
    return admin


def verifier_verrouillage(identifiant: IdentifiantConnexion) -> None:
    """Lève une exception si le compte est actuellement verrouillé."""
    if identifiant.est_verrouille and identifiant.date_verrouillage:
        temps_ecoule = datetime.utcnow() - identifiant.date_verrouillage
        if temps_ecoule < timedelta(minutes=DUREE_VERROUILLAGE_MINUTES):
            minutes_restantes = DUREE_VERROUILLAGE_MINUTES - int(temps_ecoule.total_seconds() // 60)
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Compte temporairement verrouillé après plusieurs échecs. "
                       f"Réessayez dans environ {max(minutes_restantes, 1)} minute(s).",
            )
        # Le verrouillage a expiré : on réinitialise
        identifiant.est_verrouille = False
        identifiant.tentatives_echouees = 0
        identifiant.date_verrouillage = None
