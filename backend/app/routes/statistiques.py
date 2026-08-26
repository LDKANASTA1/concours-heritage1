"""Routes de statistiques, classement et historique - au cœur de la transparence du concours."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import OPTIONS_CODES
from app.database import get_db
from app.models import HistoriqueElu, StatistiqueOption, User, Vote
from app.schemas import ClassementEntree, HistoriqueEluReponse, StatistiqueOptionReponse
from app.services.elus_service import GRAND_AMBASSADEUR

router = APIRouter(prefix="/api/statistiques", tags=["Statistiques"])


@router.get("/option/{option}", response_model=StatistiqueOptionReponse)
def statistiques_option(option: str, db: Session = Depends(get_db)):
    if option not in OPTIONS_CODES:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Option inconnue.")
    stat = db.query(StatistiqueOption).filter(StatistiqueOption.option == option).order_by(StatistiqueOption.id.desc()).first()
    if not stat:
        # Aucun vote encore : on renvoie des statistiques à zéro plutôt qu'une erreur
        total_inscrits = db.query(func.count(User.id)).filter(User.option == option).scalar() or 0
        return StatistiqueOptionReponse(
            option=option, total_votants=0, total_votes=0,
            total_inscrits=total_inscrits, taux_participation=0.0,
            elu_id=None, nb_votes_elu=0,
        )
    return stat


@router.get("/globales")
def statistiques_globales(db: Session = Depends(get_db)):
    """Vue d'ensemble utilisée par la page statistiques.html (graphiques Chart.js)."""
    resultat = []
    for code in OPTIONS_CODES:
        stat = db.query(StatistiqueOption).filter(StatistiqueOption.option == code).order_by(StatistiqueOption.id.desc()).first()
        total_inscrits = db.query(func.count(User.id)).filter(User.option == code).scalar() or 0
        resultat.append({
            "option": code,
            "total_votants": stat.total_votants if stat else 0,
            "total_votes": stat.total_votes if stat else 0,
            "total_inscrits": total_inscrits,
            "taux_participation": stat.taux_participation if stat else 0.0,
        })
    return resultat


@router.get("/classement/{option}", response_model=list[ClassementEntree])
def classement_option(option: str, db: Session = Depends(get_db)):
    """Classement complet (transparence totale) des candidats d'une option, du plus au moins voté."""
    if option not in OPTIONS_CODES:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Option inconnue.")

    resultats = (
        db.query(User, func.count(Vote.id).label("nb_votes"))
        .outerjoin(Vote, (Vote.candidat_id == User.id) & (Vote.phase == "option"))
        .filter(User.option == option, User.est_actif == True)  # noqa: E712
        .group_by(User.id)
        .order_by(func.count(Vote.id).desc())
        .all()
    )
    return [
        ClassementEntree(candidat=candidat, nb_votes=nb_votes or 0, position=i + 1)
        for i, (candidat, nb_votes) in enumerate(resultats)
    ]


@router.get("/classement-general")
def classement_general(db: Session = Depends(get_db)):
    """Le classement général = les 7 ambassadeurs d'options + l'état de la finale."""
    elus_options = (
        db.query(HistoriqueElu)
        .filter(HistoriqueElu.est_actuel == True, HistoriqueElu.option != GRAND_AMBASSADEUR)  # noqa: E712
        .all()
    )
    grand_ambassadeur = (
        db.query(HistoriqueElu)
        .filter(HistoriqueElu.est_actuel == True, HistoriqueElu.option == GRAND_AMBASSADEUR)  # noqa: E712
        .first()
    )
    return {
        "ambassadeurs_options": [
            {"option": e.option, "candidat_id": e.user_id, "nb_votes": e.nb_votes}
            for e in elus_options
        ],
        "grand_ambassadeur": (
            {"candidat_id": grand_ambassadeur.user_id, "nb_votes": grand_ambassadeur.nb_votes}
            if grand_ambassadeur else None
        ),
    }


@router.get("/historique/{option}", response_model=list[HistoriqueEluReponse])
def historique_option(option: str, db: Session = Depends(get_db)):
    """Historique complet des changements d'élu pour une option (ou GRAND_AMBASSADEUR)."""
    return (
        db.query(HistoriqueElu)
        .filter(HistoriqueElu.option == option)
        .order_by(HistoriqueElu.date_debut.desc())
        .all()
    )
