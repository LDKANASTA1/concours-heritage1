"""
Envoi d'emails via SMTP (Gmail par défaut).
Si SMTP_ENABLED=false dans le .env, les emails sont simplement ignorés (utile en développement).
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

ENTETE_STYLE = """
<div style="font-family: 'Inter', Arial, sans-serif; max-width: 560px; margin: auto;">
  <div style="background: linear-gradient(135deg, #667eea, #764ba2); padding: 24px; border-radius: 8px 8px 0 0;">
    <h2 style="color: #ffffff; margin: 0;">{nom_ecole}</h2>
    <p style="color: #ffd700; margin: 4px 0 0;">Concours des Ambassadeurs de la Promotion</p>
  </div>
  <div style="background: #ffffff; padding: 24px; border: 1px solid #eee; border-radius: 0 0 8px 8px;">
    {corps}
  </div>
</div>
"""


def _envoyer(destinataire: str, sujet: str, corps_html: str) -> bool:
    if not settings.SMTP_ENABLED:
        return False
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD or settings.SMTP_PASSWORD.startswith("REMPLACEZ"):
        # Configuration SMTP absente : on n'échoue pas silencieusement en production,
        # mais on évite de casser le flux d'inscription/vote en développement.
        return False

    message = MIMEMultipart("alternative")
    message["Subject"] = sujet
    message["From"] = settings.SMTP_FROM
    message["To"] = destinataire
    html = ENTETE_STYLE.format(nom_ecole=settings.NOM_ECOLE, corps=corps_html)
    message.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as serveur:
            serveur.starttls()
            serveur.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            serveur.sendmail(settings.SMTP_FROM, destinataire, message.as_string())
        return True
    except smtplib.SMTPException:
        return False


def envoyer_email_bienvenue(destinataire: str, prenom: str) -> bool:
    corps = f"""
    <p>Bonjour {prenom},</p>
    <p>Ta candidature au <strong>Concours des Ambassadeurs de la Promotion</strong> a bien été enregistrée.</p>
    <p>Tu peux dès maintenant te connecter pour suivre les votes et consulter les statistiques en temps réel.</p>
    <p style="color:#888; font-size: 13px;">Rappel : le vote porte sur le leadership, l'engagement et la représentativité, pas sur l'apparence physique.</p>
    """
    return _envoyer(destinataire, f"Bienvenue au concours - {settings.NOM_ECOLE}", corps)


def envoyer_email_confirmation_vote(destinataire: str, prenom: str, phase: str) -> bool:
    libelle_phase = "de ton option" if phase == "option" else "final (grand ambassadeur)"
    corps = f"""
    <p>Bonjour {prenom},</p>
    <p>Ton vote {libelle_phase} a bien été enregistré. Merci pour ta participation !</p>
    """
    return _envoyer(destinataire, "Confirmation de ton vote", corps)


def envoyer_email_elu(destinataire: str, prenom: str, option: str) -> bool:
    corps = f"""
    <p>Félicitations {prenom} !</p>
    <p>Tu es actuellement l'ambassadeur/ambassadrice élu(e) de l'option <strong>{option}</strong>.</p>
    <p>Ce statut peut évoluer jusqu'à la clôture du vote : reste engagé(e) !</p>
    """
    return _envoyer(destinataire, "Tu es actuellement élu(e) !", corps)


def envoyer_email_accuse_reception_contact(destinataire: str, nom: str) -> bool:
    corps = f"""
    <p>Bonjour {nom},</p>
    <p>Nous avons bien reçu ton message et te répondrons dans les meilleurs délais.</p>
    """
    return _envoyer(destinataire, "Accusé de réception - Contact", corps)


def envoyer_email_notification_admin_contact(nom: str, email_expediteur: str, sujet: str, message: str) -> bool:
    corps = f"""
    <p>Nouveau message reçu via le formulaire de contact :</p>
    <p><strong>De :</strong> {nom} ({email_expediteur})<br>
       <strong>Sujet :</strong> {sujet}</p>
    <p>{message}</p>
    """
    return _envoyer(settings.SUPPORT_EMAIL, f"[Contact] {sujet}", corps)
