"""Routes du centre de notifications."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Notification, User
from app.schemas import NotificationReponse

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.get("", response_model=list[NotificationReponse])
def mes_notifications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.date_creation.desc())
        .limit(100)
        .all()
    )


@router.patch("/{notification_id}/lu", response_model=NotificationReponse)
def marquer_comme_lu(notification_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notif = db.query(Notification).filter(
        Notification.id == notification_id, Notification.user_id == current_user.id
    ).first()
    if not notif:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notification introuvable.")
    notif.est_lu = True
    db.commit()
    db.refresh(notif)
    return notif


@router.post("/tout-marquer-lu")
def tout_marquer_lu(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(Notification).filter(
        Notification.user_id == current_user.id, Notification.est_lu == False  # noqa: E712
    ).update({"est_lu": True})
    db.commit()
    return {"detail": "Toutes les notifications ont été marquées comme lues."}
