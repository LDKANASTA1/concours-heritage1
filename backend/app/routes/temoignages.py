"""
Routes des témoignages de soutien.

Règles de sécurité imposées par le cadrage du projet :
- un témoignage est invisible tant qu'il n'a pas été approuvé par un administrateur (pré-modération) ;
- un même auteur ne peut laisser qu'un seul témoignage par candidat ;
- tout élève peut signaler un témoignage déjà publié, ce qui le repasse en file de modération.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_admin, get_current_user
from app.database import get_db
from app.models import Administrateur, Notification, Temoignage, User
from app.schemas import (
    TemoignageCreation, TemoignageEnAttente, TemoignageModeration,
    TemoignagePublic, TemoignageSignalement,
)

router = APIRouter(prefix="/api/temoignages", tags=["Témoignages"])

SEUIL_SIGNALEMENTS_AVANT_DEPUBLICATION = 3


@router.post("", status_code=status.HTTP_201_CREATED)
def deposer_temoignage(
    payload: TemoignageCreation,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.candidat_id == current_user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Tu ne peux pas déposer un témoignage sur ton propre profil.")

    candidat = db.query(User).filter(User.id == payload.candidat_id).first()
    if not candidat:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Candidat introuvable.")

    existant = db.query(Temoignage).filter(
        Temoignage.auteur_id == current_user.id, Temoignage.candidat_id == payload.candidat_id
    ).first()
    if existant:
        raise HTTPException(status.HTTP_409_CONFLICT, "Tu as déjà laissé un témoignage pour ce candidat.")

    temoignage = Temoignage(
        auteur_id=current_user.id, candidat_id=payload.candidat_id,
        contenu=payload.contenu, statut="en_attente",
    )
    db.add(temoignage)
    db.commit()
    return {"detail": "Ton témoignage a été soumis et sera visible après validation par un administrateur."}


@router.get("/candidat/{candidat_id}", response_model=list[TemoignagePublic])
def temoignages_approuves(candidat_id: int, db: Session = Depends(get_db)):
    """Seuls les témoignages approuvés et non signalés sont publics."""
    temoignages = (
        db.query(Temoignage)
        .filter(Temoignage.candidat_id == candidat_id, Temoignage.statut == "approuve", Temoignage.signale == False)  # noqa: E712
        .order_by(Temoignage.date_creation.desc())
        .all()
    )
    return [
        TemoignagePublic(id=t.id, auteur_prenom=t.auteur.prenom, contenu=t.contenu, date_creation=t.date_creation)
        for t in temoignages
    ]


@router.post("/{temoignage_id}/signaler")
def signaler_temoignage(
    temoignage_id: int,
    payload: TemoignageSignalement,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    temoignage = db.query(Temoignage).filter(Temoignage.id == temoignage_id).first()
    if not temoignage:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Témoignage introuvable.")

    temoignage.nb_signalements += 1
    if temoignage.nb_signalements >= SEUIL_SIGNALEMENTS_AVANT_DEPUBLICATION:
        temoignage.signale = True  # dépublication automatique en attendant la revue d'un administrateur

    db.commit()
    return {"detail": "Signalement enregistré. Merci de contribuer à un concours respectueux."}


# ---------- Modération (réservé aux administrateurs) ----------

@router.get("/moderation/en-attente", response_model=list[TemoignageEnAttente])
def liste_en_attente(current_admin: Administrateur = Depends(get_current_admin), db: Session = Depends(get_db)):
    return (
        db.query(Temoignage)
        .filter((Temoignage.statut == "en_attente") | (Temoignage.signale == True))  # noqa: E712
        .order_by(Temoignage.date_creation.asc())
        .all()
    )


@router.patch("/moderation/{temoignage_id}")
def moderer_temoignage(
    temoignage_id: int,
    payload: TemoignageModeration,
    current_admin: Administrateur = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    temoignage = db.query(Temoignage).filter(Temoignage.id == temoignage_id).first()
    if not temoignage:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Témoignage introuvable.")

    temoignage.statut = payload.statut
    temoignage.signale = False  # la revue de l'administrateur lève le signalement
    temoignage.date_moderation = datetime.utcnow()
    temoignage.modere_par = f"{current_admin.nom_complet} ({current_admin.role})"

    if payload.statut == "rejete":
        db.add(Notification(
            user_id=temoignage.auteur_id, type="moderation",
            titre="Témoignage non publié",
            message="Ton témoignage n'a pas été publié car il ne respecte pas la charte du concours.",
        ))

    db.commit()
    return {"detail": f"Témoignage {payload.statut}."}
