"""
Compteur de visiteurs du site : une seule ligne en base (id=1), incrémentée
une fois par session de navigateur (voir js/app.js côté frontend).
"""
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import VisiteSite
from app.schemas import VisiteSiteReponse

router = APIRouter(prefix="/api/visites", tags=["Visiteurs"])


def _obtenir_ou_creer_compteur(db: Session) -> VisiteSite:
    compteur = db.query(VisiteSite).filter(VisiteSite.id == 1).first()
    if not compteur:
        compteur = VisiteSite(id=1, total_visites=0)
        db.add(compteur)
        db.commit()
        db.refresh(compteur)
    return compteur


@router.get("", response_model=VisiteSiteReponse)
def obtenir_visites(db: Session = Depends(get_db)):
    """Retourne le nombre total de visites, sans l'incrémenter."""
    compteur = _obtenir_ou_creer_compteur(db)
    return compteur


@router.post("/incrementer", response_model=VisiteSiteReponse)
def incrementer_visites(db: Session = Depends(get_db)):
    """Incrémente le compteur d'une unité (appelé une fois par session côté frontend)."""
    compteur = _obtenir_ou_creer_compteur(db)
    compteur.total_visites += 1
    compteur.derniere_visite = datetime.utcnow()
    db.commit()
    db.refresh(compteur)
    return compteur
