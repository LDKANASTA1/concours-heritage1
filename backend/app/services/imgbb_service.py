import os
import cloudinary
import cloudinary.uploader
from fastapi import HTTPException, UploadFile, status

# Configuration Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

TAILLE_MAX_OCTETS = 5 * 1024 * 1024  # 5 Mo
FORMATS_ACCEPTES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}

async def upload_photo_imgbb(fichier: UploadFile) -> str:
    if fichier.content_type not in FORMATS_ACCEPTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format non accepté. Utilisez JPG, PNG ou WEBP.",
        )

    contenu = await fichier.read()
    if len(contenu) > TAILLE_MAX_OCTETS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La photo dépasse la taille maximale autorisée (5 Mo).",
        )

    try:
        # Upload du fichier (en mémoire) vers Cloudinary
        result = cloudinary.uploader.upload(contenu)
        return result["secure_url"]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erreur d'upload vers Cloudinary : {str(e)}"
        )