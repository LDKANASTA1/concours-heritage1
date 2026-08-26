"""
Crée un compte administrateur (modérateur) en ligne de commande.
Usage : python create_admin.py
Ce script n'est pas exposé publiquement : seule une personne ayant accès au serveur
peut créer un compte de modération (professeur référent, délégué désigné, direction).
"""
import getpass

from app.auth import hasher_pin
from app.database import SessionLocal, Base, engine
from app.models import Administrateur

Base.metadata.create_all(bind=engine)


def main():
    print("=== Création d'un compte administrateur (modération) ===")
    nom_complet = input("Nom complet : ").strip()
    role = input("Rôle (professeur / delegue / direction) : ").strip() or "professeur"
    email = input("Email : ").strip()
    mot_de_passe = getpass.getpass("Mot de passe : ")

    db = SessionLocal()
    try:
        if db.query(Administrateur).filter(Administrateur.email == email).first():
            print("Un administrateur avec cet email existe déjà.")
            return
        admin = Administrateur(
            nom_complet=nom_complet, role=role, email=email,
            password_hash=hasher_pin(mot_de_passe),
        )
        db.add(admin)
        db.commit()
        print(f"Compte administrateur créé pour {nom_complet} ({email}).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
