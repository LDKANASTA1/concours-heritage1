"""
Recalcule, après chaque vote, l'élu courant d'une option (ou le grand ambassadeur),
met à jour les statistiques agrégées et journalise tout changement d'élu dans l'historique.
Cette centralisation garantit la transparence demandée : le classement affiché
est toujours recalculé à partir des votes réels, jamais modifié manuellement.
"""
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import (
    HistoriqueElu, Notification, StatistiqueOption, User, Vote,
)
from app.services.email_service import envoyer_email_elu

GRAND_AMBASSADEUR = "GRAND_AMBASSADEUR"


def _classement_pour(db: Session, phase: str, option: str | None = None):
    """Retourne [(candidat_id, nb_votes), ...] trié par nombre de votes décroissant."""
    query = (
        db.query(Vote.candidat_id, func.count(Vote.id).label("nb_votes"))
        .filter(Vote.phase == phase)
    )
    if option is not None:
        query = query.filter(Vote.option_cible == option)
    return (
        query.group_by(Vote.candidat_id)
        .order_by(func.count(Vote.id).desc())
        .all()
    )


def recalculer_option(db: Session, option: str) -> None:
    classement = _classement_pour(db, "option", option)
    total_votes = sum(nb for _, nb in classement)
    total_votants = db.query(func.count(func.distinct(Vote.votant_id))).filter(
        Vote.phase == "option", Vote.option_cible == option
    ).scalar() or 0
    total_inscrits = db.query(func.count(User.id)).filter(User.option == option, User.est_actif == True).scalar() or 0  # noqa: E712

    nouvel_elu_id = classement[0][0] if classement else None
    nouvel_elu_votes = classement[0][1] if classement else 0

    _mettre_a_jour_historique(db, option, nouvel_elu_id, nouvel_elu_votes)

    stat = db.query(StatistiqueOption).filter(StatistiqueOption.option == option).order_by(StatistiqueOption.id.desc()).first()
    if stat is None:
        stat = StatistiqueOption(option=option)
        db.add(stat)
    stat.date_stat = datetime.utcnow()
    stat.total_votants = total_votants
    stat.total_votes = total_votes
    stat.elu_id = nouvel_elu_id
    stat.nb_votes_elu = nouvel_elu_votes
    stat.total_inscrits = total_inscrits
    stat.taux_participation = round((total_votants / total_inscrits) * 100, 2) if total_inscrits else 0.0

    db.commit()


def recalculer_finale(db: Session) -> None:
    classement = _classement_pour(db, "finale")
    nouvel_elu_id = classement[0][0] if classement else None
    nouvel_elu_votes = classement[0][1] if classement else 0
    _mettre_a_jour_historique(db, GRAND_AMBASSADEUR, nouvel_elu_id, nouvel_elu_votes)
    db.commit()


def _mettre_a_jour_historique(db: Session, option: str, nouvel_elu_id: int | None, nb_votes: int) -> None:
    elu_actuel = (
        db.query(HistoriqueElu)
        .filter(HistoriqueElu.option == option, HistoriqueElu.est_actuel == True)  # noqa: E712
        .first()
    )

    if elu_actuel and elu_actuel.user_id == nouvel_elu_id:
        # Pas de changement d'élu : on met juste à jour le nombre de votes
        elu_actuel.nb_votes = nb_votes
        return

    # Changement d'élu (ou premier élu) : on clôture l'ancien et on ouvre un nouveau mandat
    if elu_actuel:
        elu_actuel.est_actuel = False
        elu_actuel.date_fin = datetime.utcnow()
        _notifier(db, elu_actuel.user_id, "elu",
                  "Changement de classement",
                  "Le classement a évolué suite à de nouveaux votes. Consulte les statistiques pour voir l'état actuel.")

    if nouvel_elu_id is not None:
        nouveau = HistoriqueElu(
            option=option, user_id=nouvel_elu_id, nb_votes=nb_votes,
            date_debut=datetime.utcnow(), est_actuel=True,
        )
        db.add(nouveau)
        candidat = db.query(User).filter(User.id == nouvel_elu_id).first()
        if candidat:
            _notifier(db, candidat.id, "elu",
                      "Tu es en tête !",
                      f"Tu es actuellement en tête du classement pour {option}.")
            if candidat.email and candidat.email_verifie:
                envoyer_email_elu(candidat.email, candidat.prenom, option)


def _notifier(db: Session, user_id: int, type_notif: str, titre: str, message: str) -> None:
    db.add(Notification(user_id=user_id, type=type_notif, titre=titre, message=message))
