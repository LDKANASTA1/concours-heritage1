"""
Routes de vote - version "Ambassadeurs" : vote direct, sans duel ni restriction de genre.

Phase 1 ('option') : chaque élève vote pour un·e camarade de SA PROPRE option.
Phase 2 ('finale') : chaque élève vote pour le grand ambassadeur parmi les 7 élus d'options.
Un vote peut être modifié tant que la phase correspondante n'est pas explicitement close par un administrateur.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import HistoriqueElu, Notification, ProgressionVote, User, Vote
from app.schemas import VoteCreation, VoteReponse
from app.services.elus_service import GRAND_AMBASSADEUR, recalculer_finale, recalculer_option
from app.services.email_service import envoyer_email_confirmation_vote

router = APIRouter(prefix="/api/votes", tags=["Votes"])


def _candidats_finale(db: Session) -> list[int]:
    """Les 7 élus actuels d'options sont les seuls candidats valides en finale."""
    elus = db.query(HistoriqueElu).filter(
        HistoriqueElu.est_actuel == True,  # noqa: E712
        HistoriqueElu.option != GRAND_AMBASSADEUR,
    ).all()
    return [e.user_id for e in elus]


@router.post("", response_model=VoteReponse, status_code=status.HTTP_201_CREATED)
def voter(payload: VoteCreation, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    candidat = db.query(User).filter(User.id == payload.candidat_id, User.est_actif == True).first()  # noqa: E712
    if not candidat:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Candidat introuvable.")

    if candidat.id == current_user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Tu ne peux pas voter pour toi-même.")

    option_cible = None
    if payload.phase == "option":
        if candidat.option != current_user.option:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Tu ne peux voter, en phase 'option', que pour un candidat de ta propre option.",
            )
        option_cible = current_user.option
    else:  # phase == 'finale'
        candidats_valides = _candidats_finale(db)
        if candidat.id not in candidats_valides:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Ce candidat n'est pas (ou plus) éligible à la finale.",
            )

    vote_existant = db.query(Vote).filter(
        Vote.votant_id == current_user.id, Vote.phase == payload.phase
    ).first()

    if vote_existant:
        ancien_candidat_id = vote_existant.candidat_id
        vote_existant.candidat_id = candidat.id
        vote_existant.option_cible = option_cible
        vote = vote_existant
    else:
        vote = Vote(
            votant_id=current_user.id, candidat_id=candidat.id,
            phase=payload.phase, option_cible=option_cible,
        )
        db.add(vote)
        ancien_candidat_id = None

    progression = db.query(ProgressionVote).filter(ProgressionVote.votant_id == current_user.id).first()
    if progression:
        if payload.phase == "option":
            progression.a_vote_option = True
        else:
            progression.a_vote_finale = True

    db.add(Notification(
        user_id=candidat.id, type="vote",
        titre="Nouveau vote reçu",
        message="Tu as reçu un nouveau vote. Consulte les statistiques pour suivre ta progression.",
    ))

    db.commit()
    db.refresh(vote)

    if payload.phase == "option":
        recalculer_option(db, option_cible)
    else:
        recalculer_finale(db)

    if current_user.email and current_user.email_verifie:
        envoyer_email_confirmation_vote(current_user.email, current_user.prenom, payload.phase)

    return vote


@router.get("/mon-vote/{phase}", response_model=VoteReponse | None)
def mon_vote(phase: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if phase not in ("option", "finale"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "phase doit être 'option' ou 'finale'.")
    return db.query(Vote).filter(Vote.votant_id == current_user.id, Vote.phase == phase).first()


@router.get("/candidats-finale")
def candidats_finale(db: Session = Depends(get_db)):
    """Retourne les 7 élus actuels d'options, candidats à la finale."""
    ids = _candidats_finale(db)
    return db.query(User).filter(User.id.in_(ids)).all() if ids else []
