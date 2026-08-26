"""
Upload des photos de profil sur ImgBB.
Seul le lien retourné par ImgBB est stocké en base : aucune image n'est jamais
conservée sur le serveur de l'application.
"""
import base64

import httpx
from fastapi import HTTPException, UploadFile, status

from app.config import settings

TAILLE_MAX_OCTETS = 5 * 1024 * 1024  # 5 Mo
FORMATS_ACCEPTES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}


async def upload_photo_imgbb(fichier: UploadFile) -> str:
    """Envoie une photo à ImgBB et retourne son URL publique."""
    if fichier.content_type not in FORMATS_ACCEPTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format de photo non accepté. Utilisez JPG, PNG ou WEBP.",
        )

    contenu = await fichier.read()
    if len(contenu) > TAILLE_MAX_OCTETS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La photo dépasse la taille maximale autorisée (5 Mo).",
        )

    if not settings.IMGBB_API_KEY or settings.IMGBB_API_KEY.startswith("REMPLACEZ"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="La clé IMGBB_API_KEY n'est pas configurée côté serveur (voir fichier .env).",
        )

    image_base64 = base64.b64encode(contenu).decode("utf-8")

    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            reponse = await client.post(
                "https://api.imgbb.com/1/upload",
                data={"key": settings.IMGBB_API_KEY, "image": image_base64},
            )
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Impossible de contacter le service d'hébergement de photos. Réessayez plus tard.",
            )

    if reponse.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="L'envoi de la photo a échoué. Réessayez avec une autre image.",
        )

    data = reponse.json()
    url = data.get("data", {}).get("url")
    if not url:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Réponse inattendue du service d'hébergement de photos.",
        )
    return url
