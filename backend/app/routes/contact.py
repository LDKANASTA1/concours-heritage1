"""Routes du formulaire de contact : envoi d'emails + stockage en base."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import MessageContact
from app.schemas import MessageContactCreation
from app.services.email_service import (
    envoyer_email_accuse_reception_contact,
    envoyer_email_notification_admin_contact,
)

router = APIRouter(prefix="/api/contact", tags=["Contact"])


@router.post("", status_code=status.HTTP_201_CREATED)
def envoyer_message_contact(payload: MessageContactCreation, db: Session = Depends(get_db)):
    message = MessageContact(
        nom=payload.nom, email=payload.email, telephone=payload.telephone,
        sujet=payload.sujet, message=payload.message,
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    envoyer_email_notification_admin_contact(payload.nom, payload.email, payload.sujet, payload.message)
    envoyer_email_accuse_reception_contact(payload.email, payload.nom)

    return {"detail": "Message envoyé avec succès. Une confirmation t'a été envoyée par email."}
