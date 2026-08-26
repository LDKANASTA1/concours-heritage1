"""
Routes de partage. Le backend fournit uniquement le texte pré-formaté et l'URL WhatsApp ;
c'est le frontend qui ouvre le lien wa.me correspondant.
"""
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Partage
from app.schemas import PartageCreation

router = APIRouter(prefix="/api/share", tags=["Partage"])

MESSAGES = {
    "classement": "Suis le classement transparent du Concours des Ambassadeurs de la Promotion du {ecole} !",
    "option": "Découvre l'ambassadeur/ambassadrice actuel(le) de l'option {detail} au {ecole} !",
    "finale": "Le vote pour le Grand Ambassadeur de la Promotion du {ecole} est en cours, viens voter !",
    "accueil": "Participe au Concours des Ambassadeurs de la Promotion du {ecole} !",
}


@router.get("/message/{type_page}")
def message_partage(type_page: str, detail: str = ""):
    if type_page not in MESSAGES:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Type de page inconnu pour le partage.")
    texte = MESSAGES[type_page].format(ecole=settings.NOM_ECOLE, detail=detail)
    return {
        "texte": texte,
        "lien_whatsapp": f"https://wa.me/?text={quote(texte)}",
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def enregistrer_partage(payload: PartageCreation, db: Session = Depends(get_db)):
    """Journalise un partage (statistique de portée, pas d'identification obligatoire)."""
    partage = Partage(
        type_partage=payload.type_partage,
        page_partagee=payload.page_partagee,
        url_partage=payload.url_partage,
    )
    db.add(partage)
    db.commit()
    return {"detail": "Partage enregistré."}
