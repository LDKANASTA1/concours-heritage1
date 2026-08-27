"""
Modèles SQLAlchemy pour le "Concours des Ambassadeurs de la Promotion".

Par rapport au projet initial, cette version :
- retire la table votes_finaux (plus de duels/matchs 1 contre 1)
- retire la table versions (plus nécessaire sans système de matchs)
- ajoute le champ `presentation` sur users (candidature écrite obligatoire)
- ajoute le champ `phase` sur votes ('option' ou 'finale') pour un vote direct en 2 tours
- ajoute la table temoignages, avec pré-modération et signalement
- supprime toute restriction de vote basée sur le genre
"""
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """Élève inscrit au concours (candidat et/ou votant)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    photo_url = Column(String(500), nullable=False)  # lien ImgBB
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    classe = Column(String(50), nullable=False)
    option = Column(String(100), nullable=False, index=True)
    numero = Column(String(20), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    genre = Column(String(10), nullable=False)  # conservé pour les statistiques uniquement,
    # jamais utilisé pour restreindre qui peut voter pour qui
    presentation = Column(Text, nullable=False)  # candidature écrite (50-100 mots), obligatoire
    date_inscription = Column(DateTime, default=datetime.utcnow)
    est_actif = Column(Boolean, default=True)
    email_verifie = Column(Boolean, default=False)

    identifiant_connexion = relationship("IdentifiantConnexion", back_populates="user", uselist=False, cascade="all, delete-orphan")
    votes_emis = relationship("Vote", foreign_keys="Vote.votant_id", back_populates="votant", cascade="all, delete-orphan")
    votes_recus = relationship("Vote", foreign_keys="Vote.candidat_id", back_populates="candidat", cascade="all, delete-orphan")


class IdentifiantConnexion(Base):
    """Table séparée pour les informations sensibles de connexion (sécurité)."""
    __tablename__ = "identifiants_connexion"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    numero = Column(String(20), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    date_derniere_connexion = Column(DateTime, nullable=True)
    tentatives_echouees = Column(Integer, default=0)
    est_verrouille = Column(Boolean, default=False)
    date_verrouillage = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="identifiant_connexion")


class Vote(Base):
    """
    Vote direct (sans duel). phase='option' : vote pour un candidat de sa propre option.
    phase='finale' : vote pour le grand ambassadeur parmi les 7 élus d'options.
    Un votant ne peut voter qu'une fois par phase (il peut changer son vote tant que la phase est ouverte).
    """
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, index=True)
    votant_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    candidat_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    phase = Column(String(20), nullable=False, default="option")  # 'option' ou 'finale'
    option_cible = Column(String(100), nullable=True)  # rempli en phase 'option'
    date_vote = Column(DateTime, default=datetime.utcnow)

    votant = relationship("User", foreign_keys=[votant_id], back_populates="votes_emis")
    candidat = relationship("User", foreign_keys=[candidat_id], back_populates="votes_recus")

    __table_args__ = (
        UniqueConstraint("votant_id", "phase", name="uq_un_vote_par_phase"),
    )


class HistoriqueElu(Base):
    """Historique de tous les ambassadeurs élus (options + grand ambassadeur), avec dates de mandat."""
    __tablename__ = "historique_elus"

    id = Column(Integer, primary_key=True, index=True)
    option = Column(String(100), nullable=False)  # nom de l'option, ou 'GRAND_AMBASSADEUR'
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    nb_votes = Column(Integer, nullable=False)
    date_debut = Column(DateTime, nullable=False, default=datetime.utcnow)
    date_fin = Column(DateTime, nullable=True)
    est_actuel = Column(Boolean, default=True)

    candidat = relationship("User")


class StatistiqueOption(Base):
    """Statistiques agrégées par option, recalculées à chaque vote."""
    __tablename__ = "statistiques_options"

    id = Column(Integer, primary_key=True, index=True)
    option = Column(String(100), nullable=False, index=True)
    date_stat = Column(DateTime, default=datetime.utcnow)
    total_votants = Column(Integer, default=0)
    total_votes = Column(Integer, default=0)
    elu_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    nb_votes_elu = Column(Integer, default=0)
    taux_participation = Column(Float, default=0.0)
    total_inscrits = Column(Integer, default=0)

    elu = relationship("User")


class HistoriqueClassement(Base):
    """Photo du classement à un instant T, conservée pour la transparence et les tendances."""
    __tablename__ = "historique_classement"

    id = Column(Integer, primary_key=True, index=True)
    option = Column(String(100), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    position = Column(Integer, nullable=False)
    nb_votes = Column(Integer, nullable=False)
    date_enregistrement = Column(DateTime, default=datetime.utcnow)

    candidat = relationship("User")


class ProgressionVote(Base):
    """Suivi de la progression d'un votant à travers les deux phases (options -> finale)."""
    __tablename__ = "progression_vote"

    id = Column(Integer, primary_key=True, index=True)
    votant_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    a_vote_option = Column(Boolean, default=False)
    a_vote_finale = Column(Boolean, default=False)
    phase_actuelle = Column(String(20), default="option")  # 'option' ou 'finale'
    date_mise_a_jour = Column(DateTime, default=datetime.utcnow)

    votant = relationship("User")


class Notification(Base):
    """Notifications envoyées à un élève (vote reçu, élu, système, info)."""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False)  # 'vote', 'elu', 'systeme', 'info', 'moderation'
    titre = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    est_lu = Column(Boolean, default=False)
    date_creation = Column(DateTime, default=datetime.utcnow)
    lien = Column(String(500), nullable=True)


class Session(Base):
    """Sessions actives (utile pour la révocation anticipée de jetons si besoin)."""
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(500), unique=True, nullable=False)
    date_creation = Column(DateTime, default=datetime.utcnow)
    date_expiration = Column(DateTime, nullable=False)
    ip_adresse = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)


class MessageContact(Base):
    """Messages envoyés via le formulaire de contact public."""
    __tablename__ = "messages_contact"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    telephone = Column(String(20), nullable=True)
    sujet = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    date_envoi = Column(DateTime, default=datetime.utcnow)
    est_lu = Column(Boolean, default=False)
    date_lecture = Column(DateTime, nullable=True)
    reponse = Column(Text, nullable=True)
    date_reponse = Column(DateTime, nullable=True)


class Partage(Base):
    """Journal des partages (WhatsApp, Facebook...) pour mesurer la portée."""
    __tablename__ = "partages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    type_partage = Column(String(50), nullable=False)  # 'whatsapp', 'facebook', 'email'
    page_partagee = Column(String(255), nullable=False)
    url_partage = Column(String(500), nullable=False)
    date_partage = Column(DateTime, default=datetime.utcnow)
    nb_clics = Column(Integer, default=0)


class LogSysteme(Base):
    """Journal d'audit : trace les actions sensibles pour garantir la transparence du concours."""
    __tablename__ = "logs_systeme"

    id = Column(Integer, primary_key=True, index=True)
    utilisateur_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)
    details = Column(Text, nullable=True)
    ip_adresse = Column(String(45), nullable=True)
    date_action = Column(DateTime, default=datetime.utcnow)


class Temoignage(Base):
    """
    Message de soutien qu'un élève peut laisser sur le profil d'un candidat.
    Pré-modéré : invisible tant qu'un administrateur (professeur/délégué) ne l'a pas approuvé.
    Limité à un témoignage par (auteur, candidat).
    """
    __tablename__ = "temoignages"

    id = Column(Integer, primary_key=True, index=True)
    auteur_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    candidat_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    contenu = Column(String(280), nullable=False)  # volontairement court, façon "carte de vœux"
    statut = Column(String(20), default="en_attente")  # 'en_attente', 'approuve', 'rejete'
    signale = Column(Boolean, default=False)
    nb_signalements = Column(Integer, default=0)
    date_creation = Column(DateTime, default=datetime.utcnow)
    date_moderation = Column(DateTime, nullable=True)
    modere_par = Column(String(100), nullable=True)  # nom/rôle du modérateur (prof, délégué...)

    auteur = relationship("User", foreign_keys=[auteur_id])
    candidat = relationship("User", foreign_keys=[candidat_id])

    __table_args__ = (
        UniqueConstraint("auteur_id", "candidat_id", name="uq_un_temoignage_par_candidat"),
    )


class Administrateur(Base):
    """
    Compte de modération (professeur ou délégué de classe désigné).
    Distinct des élèves : peut approuver/rejeter les témoignages et traiter les signalements.
    """
    __tablename__ = "administrateurs"

    id = Column(Integer, primary_key=True, index=True)
    nom_complet = Column(String(150), nullable=False)
    role = Column(String(50), nullable=False)  # 'professeur', 'delegue', 'direction'
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    est_actif = Column(Boolean, default=True)
    date_creation = Column(DateTime, default=datetime.utcnow)


class VisiteSite(Base):
    """
    Compteur global de visites du site (une seule ligne en base, id=1).
    Incrémenté une fois par session de navigateur côté frontend (voir js/app.js).
    """
    __tablename__ = "visites_site"

    id = Column(Integer, primary_key=True, index=True)
    total_visites = Column(Integer, default=0, nullable=False)
    derniere_visite = Column(DateTime, default=datetime.utcnow)
