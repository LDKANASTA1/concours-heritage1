"""Routes d'inscription et de connexion."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth import (
    MAX_TENTATIVES,
    creer_token_acces,
    hasher_pin,
    verifier_pin,
    verifier_verrouillage,
)
from app.config import OPTIONS_CODES
from app.database import get_db
from app.models import IdentifiantConnexion, LogSysteme, ProgressionVote, User
from app.schemas import Token, UserConnexion, UserInscription, UserProfil
from app.services.email_service import envoyer_email_bienvenue

router = APIRouter(prefix="/api/auth", tags=["Authentification"])


@router.post("/inscription", response_model=Token, status_code=status.HTTP_201_CREATED)
def inscription(payload: UserInscription, request: Request, db: Session = Depends(get_db)):
    if payload.option not in OPTIONS_CODES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Option invalide. Options valides : {OPTIONS_CODES}")

    if db.query(User).filter(User.numero == payload.numero).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Un compte existe déjà avec ce numéro de téléphone.")

    if payload.email and db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Un compte existe déjà avec cet email.")

    pin_hash = hasher_pin(payload.pin)

    user = User(
        photo_url=payload.photo_url,
        nom=payload.nom,
        prenom=payload.prenom,
        age=payload.age,
        classe=payload.classe,
        option=payload.option,
        numero=payload.numero,
        email=payload.email,
        password_hash=pin_hash,
        genre=payload.genre,
        presentation=payload.presentation,
    )
    db.add(user)
    db.flush()  # pour obtenir user.id avant le commit

    db.add(IdentifiantConnexion(user_id=user.id, numero=payload.numero, password_hash=pin_hash))
    db.add(ProgressionVote(votant_id=user.id))
    db.add(LogSysteme(
        utilisateur_id=user.id, action="inscription",
        details=f"Inscription option={payload.option}",
        ip_adresse=request.client.host if request.client else None,
    ))
    db.commit()
    db.refresh(user)

    if user.email:
        envoyer_email_bienvenue(user.email, user.prenom)

    token = creer_token_acces(user.id)
    return Token(access_token=token, profil=UserProfil.model_validate(user))


@router.post("/connexion", response_model=Token)
def connexion(payload: UserConnexion, request: Request, db: Session = Depends(get_db)):
    from app.utils.validators import valider_numero_rdc
    try:
        numero = valider_numero_rdc(payload.numero)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))

    identifiant = db.query(IdentifiantConnexion).filter(IdentifiantConnexion.numero == numero).first()
    erreur_generique = HTTPException(status.HTTP_401_UNAUTHORIZED, "Numéro ou PIN incorrect.")

    if not identifiant:
        raise erreur_generique

    verifier_verrouillage(identifiant)

    if not verifier_pin(payload.pin, identifiant.password_hash):
        identifiant.tentatives_echouees += 1
        if identifiant.tentatives_echouees >= MAX_TENTATIVES:
            identifiant.est_verrouille = True
            identifiant.date_verrouillage = datetime.utcnow()
        db.commit()
        raise erreur_generique

    identifiant.tentatives_echouees = 0
    identifiant.est_verrouille = False
    identifiant.date_verrouillage = None
    identifiant.date_derniere_connexion = datetime.utcnow()

    user = db.query(User).filter(User.id == identifiant.user_id).first()
    if not user or not user.est_actif:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Ce compte est désactivé.")

    db.add(LogSysteme(
        utilisateur_id=user.id, action="connexion",
        ip_adresse=request.client.host if request.client else None,
    ))
    db.commit()

    token = creer_token_acces(user.id)
    return Token(access_token=token, profil=UserProfil.model_validate(user))
