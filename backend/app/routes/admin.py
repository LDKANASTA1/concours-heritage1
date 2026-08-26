"""
Routes d'authentification pour les comptes de modération (professeur référent / délégué désigné).
Ces comptes ne sont PAS créés via une route publique : ils doivent être créés directement
en base par la personne responsable du déploiement (voir README, section "Créer un administrateur").
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import creer_token_admin, verifier_pin
from app.database import get_db
from app.models import Administrateur
from app.schemas import AdminConnexion, AdminToken

router = APIRouter(prefix="/api/admin", tags=["Administration"])


@router.post("/connexion", response_model=AdminToken)
def connexion_admin(payload: AdminConnexion, db: Session = Depends(get_db)):
    admin = db.query(Administrateur).filter(Administrateur.email == payload.email).first()
    if not admin or not verifier_pin(payload.mot_de_passe, admin.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email ou mot de passe incorrect.")
    if not admin.est_actif:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Ce compte administrateur est désactivé.")

    token = creer_token_admin(admin.id)
    return AdminToken(access_token=token, nom_complet=admin.nom_complet, role=admin.role)
