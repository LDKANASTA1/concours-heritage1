"""
Lance le serveur de développement.
En production, préférez : uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
(voir README, section "Déploiement en production").
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
