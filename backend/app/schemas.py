"""Schémas Pydantic : définissent ce que l'API accepte en entrée et renvoie en sortie."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.utils.validators import valider_numero_rdc, valider_pin


# ---------- Utilisateurs ----------

class UserInscription(BaseModel):
    photo_url: str = Field(..., description="URL ImgBB de la photo, obtenue via /users/upload-photo")
    nom: str = Field(..., min_length=2, max_length=100)
    prenom: str = Field(..., min_length=2, max_length=100)
    age: int = Field(..., ge=14, le=25)
    classe: str = Field(..., min_length=2, max_length=50)
    option: str
    numero: str
    email: Optional[EmailStr] = None
    pin: str = Field(..., description="Code PIN à 4 chiffres")
    genre: str
    presentation: str = Field(..., min_length=50, max_length=800, description="Candidature écrite (50-100 mots environ)")
    consentement_parental: bool = Field(..., description="Doit être True : autorisation d'un parent/tuteur")
    charte_acceptee: bool = Field(..., description="Doit être True : acceptation de la charte de bonne conduite")

    @field_validator("numero")
    @classmethod
    def check_numero(cls, v):
        return valider_numero_rdc(v)

    @field_validator("pin")
    @classmethod
    def check_pin(cls, v):
        return valider_pin(v)

    @field_validator("genre")
    @classmethod
    def check_genre(cls, v):
        if v not in ("masculin", "féminin"):
            raise ValueError("genre doit être 'masculin' ou 'féminin'")
        return v

    @field_validator("consentement_parental")
    @classmethod
    def check_consentement(cls, v):
        if not v:
            raise ValueError("Le consentement parental est obligatoire pour s'inscrire au concours.")
        return v

    @field_validator("charte_acceptee")
    @classmethod
    def check_charte(cls, v):
        if not v:
            raise ValueError("L'acceptation de la charte de bonne conduite est obligatoire.")
        return v


class UserConnexion(BaseModel):
    numero: str
    pin: str


class UserProfil(BaseModel):
    id: int
    photo_url: str
    nom: str
    prenom: str
    age: int
    classe: str
    option: str
    presentation: str
    genre: str
    date_inscription: datetime

    model_config = {"from_attributes": True}


class UserProfilModification(BaseModel):
    # L'option et le genre ne sont volontairement pas modifiables ici (cohérence du concours)
    nom: Optional[str] = Field(None, min_length=2, max_length=100)
    prenom: Optional[str] = Field(None, min_length=2, max_length=100)
    classe: Optional[str] = Field(None, min_length=2, max_length=50)
    presentation: Optional[str] = Field(None, min_length=50, max_length=800)
    email: Optional[EmailStr] = None


class CandidatPublic(BaseModel):
    """Ce que voient les votants : jamais l'identifiant de connexion, le PIN, etc."""
    id: int
    photo_url: str
    nom: str
    prenom: str
    classe: str
    option: str
    presentation: str

    model_config = {"from_attributes": True}


# ---------- Authentification ----------

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    profil: UserProfil


# ---------- Votes ----------

class VoteCreation(BaseModel):
    candidat_id: int
    phase: str = Field(..., description="'option' ou 'finale'")

    @field_validator("phase")
    @classmethod
    def check_phase(cls, v):
        if v not in ("option", "finale"):
            raise ValueError("phase doit être 'option' ou 'finale'")
        return v


class VoteReponse(BaseModel):
    id: int
    candidat_id: int
    phase: str
    date_vote: datetime

    model_config = {"from_attributes": True}


# ---------- Statistiques ----------

class StatistiqueOptionReponse(BaseModel):
    option: str
    total_votants: int
    total_votes: int
    total_inscrits: int
    taux_participation: float
    elu_id: Optional[int] = None
    nb_votes_elu: int

    model_config = {"from_attributes": True}


class ClassementEntree(BaseModel):
    candidat: CandidatPublic
    nb_votes: int
    position: int


# ---------- Historique ----------

class HistoriqueEluReponse(BaseModel):
    option: str
    user_id: int
    nb_votes: int
    date_debut: datetime
    date_fin: Optional[datetime] = None
    est_actuel: bool

    model_config = {"from_attributes": True}


# ---------- Contact ----------

class MessageContactCreation(BaseModel):
    nom: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    telephone: Optional[str] = None
    sujet: str = Field(..., min_length=2, max_length=255)
    message: str = Field(..., min_length=5)


# ---------- Partage ----------

class PartageCreation(BaseModel):
    type_partage: str = Field(..., description="'whatsapp', 'facebook' ou 'email'")
    page_partagee: str
    url_partage: str


# ---------- Notifications ----------

class NotificationReponse(BaseModel):
    id: int
    type: str
    titre: str
    message: str
    est_lu: bool
    date_creation: datetime
    lien: Optional[str] = None

    model_config = {"from_attributes": True}


# ---------- Témoignages ----------

class TemoignageCreation(BaseModel):
    candidat_id: int
    contenu: str = Field(..., min_length=3, max_length=280)


class TemoignagePublic(BaseModel):
    id: int
    auteur_prenom: str
    contenu: str
    date_creation: datetime

    model_config = {"from_attributes": True}


class TemoignageSignalement(BaseModel):
    raison: Optional[str] = Field(None, max_length=280)


class TemoignageModeration(BaseModel):
    statut: str = Field(..., description="'approuve' ou 'rejete'")

    @field_validator("statut")
    @classmethod
    def check_statut(cls, v):
        if v not in ("approuve", "rejete"):
            raise ValueError("statut doit être 'approuve' ou 'rejete'")
        return v


class TemoignageEnAttente(BaseModel):
    id: int
    auteur_id: int
    candidat_id: int
    contenu: str
    signale: bool
    nb_signalements: int
    date_creation: datetime

    model_config = {"from_attributes": True}


# ---------- Administration (modération) ----------

class AdminConnexion(BaseModel):
    email: EmailStr
    mot_de_passe: str


class AdminToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    nom_complet: str
    role: str


# ---------- Compteur de visiteurs ----------

class VisiteSiteReponse(BaseModel):
    total_visites: int
