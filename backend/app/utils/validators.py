"""Validations spécifiques : numéro de téléphone RDC, PIN à 4 chiffres."""
import re

# Préfixes mobiles courants en RDC (liste non exhaustive, à ajuster si besoin)
PREFIXES_RDC = ("05", "06", "08", "09")


def valider_numero_rdc(numero: str) -> str:
    """
    Accepte les formats +243XXXXXXXXX ou 0XXXXXXXXX.
    Retourne le numéro normalisé au format +243XXXXXXXXX.
    """
    numero = numero.strip().replace(" ", "").replace("-", "")

    if numero.startswith("+243"):
        chiffres = numero[4:]
        if not (chiffres.isdigit() and len(chiffres) == 9):
            raise ValueError("Numéro invalide : format attendu +243XXXXXXXXX (9 chiffres après +243).")
        return "+243" + chiffres

    if numero.startswith("243") and len(numero) == 12:
        chiffres = numero[3:]
        return "+243" + chiffres

    if numero.startswith("0") and len(numero) == 10 and numero.isdigit():
        if not numero.startswith(PREFIXES_RDC):
            raise ValueError(f"Numéro invalide : le préfixe doit être l'un de {PREFIXES_RDC}.")
        return "+243" + numero[1:]

    raise ValueError("Numéro de téléphone invalide. Formats acceptés : 0XXXXXXXXX ou +243XXXXXXXXX.")


def valider_pin(pin: str) -> str:
    """Le PIN doit être une chaîne d'exactement 4 chiffres."""
    if not re.fullmatch(r"\d{4}", pin):
        raise ValueError("Le PIN doit être composé exactement de 4 chiffres.")
    return pin
