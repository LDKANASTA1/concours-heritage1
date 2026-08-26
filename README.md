# Concours des Ambassadeurs de la Promotion — Complexe Scolaire HERITAGE 1

Site web complet (backend FastAPI + frontend HTML/CSS/JS) pour élire, de façon
directe et transparente, un ambassadeur par option puis un Grand Ambassadeur
de la promotion (6e des humanités).

## À propos de cette version du projet

Ce projet est une évolution volontairement différente d'un « concours de la
plus belle photo ». Le vote ne porte jamais sur l'apparence physique :

- chaque candidat dépose une **photo + une candidature écrite** (leadership,
  engagement, esprit d'équipe) ;
- le vote est **direct** (pas de duels ni de matchs 1 contre 1) ;
- **aucune restriction de genre** sur qui peut voter pour qui ;
- les témoignages de soutien sont **pré-modérés** par un professeur référent
  ou un délégué désigné avant publication, et peuvent être signalés.

Si vous cherchez à réintroduire des duels photo, un classement basé sur
l'apparence, ou une restriction de vote par genre, ce n'est pas ce que ce
code fait — et ce n'est volontairement pas quelque chose que je recommande
d'ajouter, y compris pour un usage scolaire.

## Différences avec un « concours de beauté » classique (choix techniques)

| Élément | Ce projet |
|---|---|
| Contenu de candidature | Photo **+** texte de présentation obligatoire |
| Mécanique de vote | Vote direct à un tour (pas de duels/matchs) |
| Restriction de genre | Aucune |
| Modération | Témoignages pré-modérés + signalement |
| Pages « option-X.html » | Une seule page générique `option-detail.html?code=MG` (plus simple à maintenir que 7 pages dupliquées) |

## Architecture

```
projet-ambassadeurs-heritage1/
├── backend/            API FastAPI (Python)
│   ├── app/
│   │   ├── main.py, config.py, database.py, models.py, schemas.py, auth.py
│   │   ├── routes/     auth, users, votes, statistiques, contact, share, notifications, temoignages, admin
│   │   ├── services/   imgbb_service, email_service, elus_service
│   │   └── utils/      validators (téléphone RDC, PIN)
│   ├── .env.example    modèle de configuration (copier en .env)
│   ├── requirements.txt
│   ├── run.py          lancement en développement
│   ├── create_admin.py création d'un compte de modération
│   └── Dockerfile
├── frontend/           HTML/CSS/JS statique, aucune dépendance de build
│   ├── index.html
│   ├── pages/          15 pages (voir liste ci-dessous)
│   ├── css/, js/
│   └── assets/
├── docker-compose.yml  déploiement optionnel (Postgres + backend + frontend statique)
└── README.md
```

### Pages du frontend

`index.html`, puis dans `pages/` : `login`, `inscription`, `dashboard`,
`vote-option`, `vote-finale`, `classement`, `statistiques`, `historique`,
`profil`, `options`, `option-detail` (générique, paramètre `?code=`),
`reglements`, `contact`, `notifications`, `mentions`.

## Installation en développement (démarrage rapide)

### 1. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows : venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # puis ouvrez .env et remplacez au minimum IMGBB_API_KEY
python run.py
```

L'API tourne sur `http://localhost:8000`. Documentation interactive :
`http://localhost:8000/docs`.

Par défaut, `DATABASE_URL` pointe vers un fichier SQLite local
(`heritage1.db`) : aucune installation de base de données n'est nécessaire
pour tester le projet entre élèves.

### 2. Frontend

Aucune compilation nécessaire. Le plus simple :

```bash
cd frontend
python3 -m http.server 5500
```

Puis ouvrez `http://localhost:5500`. Si votre API tourne sur une autre URL,
changez la ligne `window.HERITAGE1_API_URL = "http://localhost:8000";`
présente en haut de chaque page HTML.

### 3. Créer un compte de modération (professeur référent / délégué)

Les comptes administrateurs ne peuvent pas être créés depuis le site public
(volontairement, pour éviter tout détournement) :

```bash
cd backend
python create_admin.py
```

Renseignez le nom, le rôle et un email/mot de passe. Utilisez ensuite
`POST /api/admin/connexion` (voir `/docs`) pour obtenir un jeton et modérer
les témoignages via `/api/temoignages/moderation/...`.

## Configuration à remplacer avant tout déploiement réel

Dans `backend/.env` :

| Variable | À faire |
|---|---|
| `IMGBB_API_KEY` | Créez une clé gratuite sur https://api.imgbb.com/ |
| `SECRET_KEY` | Générez une valeur aléatoire : `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DATABASE_URL` | En production, remplacez par l'URL PostgreSQL de votre hébergeur (ex. ElephantSQL) |
| `SMTP_USER` / `SMTP_PASSWORD` | Créez un « mot de passe d'application » Gmail : https://myaccount.google.com/apppasswords |
| `FRONTEND_URL` | URL réelle de votre frontend déployé (utilisée pour la configuration CORS) |

## Déploiement en production

### Option A — Manuelle

1. Provisionnez une base PostgreSQL (ex. ElephantSQL, plan gratuit) et copiez
   son URL dans `DATABASE_URL`.
2. Déployez le dossier `backend/` sur un service Python (Render, Railway,
   PythonAnywhere...) avec la commande de démarrage :
   `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
3. Déployez le dossier `frontend/` sur un hébergeur statique (Netlify,
   Vercel, GitHub Pages...).
4. Mettez à jour `window.HERITAGE1_API_URL` dans les pages HTML avec l'URL
   réelle de votre backend, et `FRONTEND_URL` dans `.env` avec l'URL réelle
   de votre frontend.

### Option B — Docker Compose (backend + PostgreSQL + frontend statique)

```bash
docker compose up --build
```

Le backend écoute sur `:8000`, PostgreSQL sur `:5432`, le frontend statique
sur `:5500`. Pensez à changer les mots de passe par défaut dans
`docker-compose.yml` avant tout déploiement réel.

## Migrations de schéma (Alembic)

`Base.metadata.create_all()` crée les tables manquantes au démarrage, ce qui
suffit pour un premier déploiement. Pour toute évolution ultérieure du schéma
en production (ajout de colonne, etc.), utilisez Alembic plutôt que de
modifier les tables à la main :

```bash
cd backend
alembic init alembic   # une seule fois
# configurez alembic.ini et alembic/env.py pour pointer vers app.database.Base
alembic revision --autogenerate -m "description du changement"
alembic upgrade head
```

## Sécurité déjà en place

- PIN à 4 chiffres hashé avec bcrypt (jamais stocké en clair).
- Verrouillage de compte après 3 tentatives échouées (15 minutes).
- Rate limiting sur les routes d'authentification (5 tentatives/minute).
- JWT avec expiration à 7 jours, jeton admin séparé (12h).
- Table `identifiants_connexion` séparée de `users` pour isoler les données sensibles.
- Journal d'audit (`logs_systeme`) sur les actions sensibles.
- Validation stricte des numéros de téléphone RDC et des PIN.
- Aucune photo n'est stockée sur le serveur : uniquement le lien ImgBB.

**Avant un déploiement réel**, faites relire la configuration (CORS, secrets,
HTTPS) par une personne à l'aise avec le déploiement web, et testez
l'ensemble du parcours (inscription → vote → classement) avec quelques
comptes de test.

## Support

- Email : ldkanasta@gmail.com
- WhatsApp : +243 826 740 490
