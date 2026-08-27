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
    print(f"📸 Upload de la photo : {fichier.filename}, type: {fichier.content_type}")

    if fichier.content_type not in FORMATS_ACCEPTES:
        print(f"❌ Format non accepté : {fichier.content_type}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format de photo non accepté. Utilisez JPG, PNG ou WEBP.",
        )

    contenu = await fichier.read()
    print(f"📏 Taille du fichier : {len(contenu)} octets")

    if len(contenu) > TAILLE_MAX_OCTETS:
        print(f"❌ Taille trop grande : {len(contenu)} > {TAILLE_MAX_OCTETS}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La photo dépasse la taille maximale autorisée (5 Mo).",
        )

    if not settings.IMGBB_API_KEY or settings.IMGBB_API_KEY.startswith("REMPLACEZ"):
        print("❌ Clé API ImgBB non configurée")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="La clé IMGBB_API_KEY n'est pas configurée côté serveur (voir fichier .env).",
        )

    print(f"🔑 Clé API ImgBB : {settings.IMGBB_API_KEY[:10]}... (longueur: {len(settings.IMGBB_API_KEY)})")

    image_base64 = base64.b64encode(contenu).decode("utf-8")
    print(f"📤 Image encodée en base64 : {len(image_base64)} caractères")

    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            print("📤 Envoi de la requête à ImgBB...")
            reponse = await client.post(
                "https://api.imgbb.com/1/upload",
                data={"key": settings.IMGBB_API_KEY, "image": image_base64},
            )
            print(f"📥 Réponse HTTP d'ImgBB : {reponse.status_code}")
            print(f"📥 Contenu de la réponse : {reponse.text[:200]}...")
        except httpx.RequestError as e:
            print(f"❌ Erreur réseau vers ImgBB : {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Impossible de contacter le service d'hébergement de photos. Réessayez plus tard.",
            )

    if reponse.status_code != 200:
        print(f"❌ Erreur HTTP ImgBB : {reponse.status_code} - {reponse.text}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="L'envoi de la photo a échoué. Réessayez avec une autre image.",
        )

    data = reponse.json()
    url = data.get("data", {}).get("url")
    if not url:
        print(f"❌ Réponse inattendue d'ImgBB : {data}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Réponse inattendue du service d'hébergement de photos.",
        )
    print(f"✅ Upload réussi ! URL : {url[:50]}...")
    return url