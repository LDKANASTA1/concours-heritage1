"""
Point d'entrée de l'API FastAPI.
Documentation interactive auto-générée disponible sur /docs (Swagger) et /redoc.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.database import Base, engine
from app.routes import (
    admin,
    auth,
    contact,
    notifications,
    share,
    statistiques,
    temoignages,
    users,
    visites,
    votes,
)

# Crée toutes les tables si elles n'existent pas encore.
# Pour des évolutions ultérieures du schéma en production, utilisez Alembic plutôt que
# de modifier les tables existantes à la main (voir README, section "Migrations").
Base.metadata.create_all(bind=engine)

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Concours des Ambassadeurs de la Promotion - Complexe Scolaire HERITAGE 1",
    description=(
        "API du concours des ambassadeurs de la promotion (6e des humanités). "
        "Vote direct sur candidature écrite + photo, sans duels ni restriction de genre."
    ),
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS : liste des origines explicitement autorisées à appeler cette API.
# On inclut TOUJOURS l'URL GitHub Pages réelle du projet en dur, en plus de
# settings.FRONTEND_URL, pour ne pas dépendre uniquement d'une variable
# d'environnement bien réglée sur Render (une erreur de config y a déjà cassé
# les appels API depuis le frontend une fois : mieux vaut une valeur de secours fiable).
ORIGINES_AUTORISEES = {
    settings.FRONTEND_URL,
    "https://ldkanasta1.github.io",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "https://ldkanasta1.github.io/concours-heritage1/"
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else list(ORIGINES_AUTORISEES),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting renforcé sur les endpoints d'authentification (5 tentatives/minute)
#limiter.limit("5/minute")(auth.router)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(votes.router)
app.include_router(statistiques.router)
app.include_router(contact.router)
app.include_router(share.router)
app.include_router(notifications.router)
app.include_router(temoignages.router)
app.include_router(admin.router)
app.include_router(visites.router)


@app.get("/", tags=["Santé"])
def racine():
    return {
        "message": f"API du Concours des Ambassadeurs de la Promotion - {settings.NOM_ECOLE}",
        "documentation": "/docs",
    }


@app.get("/api/sante", tags=["Santé"])
def sante():
    return {"statut": "ok"}
