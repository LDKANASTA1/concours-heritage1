"""Routes liées au profil utilisateur et à la découverte des candidats."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import OPTIONS_DISPONIBLES
from app.database import get_db
from app.models import User
from app.schemas import CandidatPublic, UserProfil, UserProfilModification
from app.services.imgbb_service import upload_photo_imgbb

router = APIRouter(prefix="/api/users", tags=["Utilisateurs"])


@router.get("/options")
def lister_options():
    """Liste des 7 options du Complexe Scolaire HERITAGE 1."""
    return OPTIONS_DISPONIBLES


@router.post("/upload-photo")
async def upload_photo(fichier: UploadFile):
    """
    Étape 1 de l'inscription : envoyer la photo pour obtenir son URL ImgBB,
    à réutiliser ensuite dans /api/auth/inscription.
    """
    url = await upload_photo_imgbb(fichier)
    return {"photo_url": url}


@router.get("/moi", response_model=UserProfil)
def mon_profil(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/moi", response_model=UserProfil)
def modifier_profil(
    payload: UserProfilModification,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Option et genre ne sont volontairement pas modifiables via ce endpoint.
    for champ, valeur in payload.model_dump(exclude_unset=True).items():
        setattr(current_user, champ, valeur)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.delete("/moi", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_mon_compte(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Suppression du compte (cascade sur les votes, témoignages, notifications, etc.)."""
    db.delete(current_user)
    db.commit()


@router.get("/candidats/{option}", response_model=list[CandidatPublic])
def candidats_par_option(option: str, db: Session = Depends(get_db)):
    """Liste des candidats d'une option, pour la page de vote correspondante."""
    candidats = db.query(User).filter(User.option == option, User.est_actif == True).all()  # noqa: E712
    if not candidats:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Aucun candidat trouvé pour cette option.")
    return candidats


@router.get("/candidats/{option}/{candidat_id}", response_model=CandidatPublic)
def detail_candidat(option: str, candidat_id: int, db: Session = Depends(get_db)):
    candidat = db.query(User).filter(User.id == candidat_id, User.option == option).first()
    if not candidat:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Candidat introuvable.")
    return candidat
