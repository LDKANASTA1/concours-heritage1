/**
 * auth.js - gère les formulaires de connexion et d'inscription (candidature).
 */

function stockerSession(token, profil) {
  localStorage.setItem("h1_token", token);
  localStorage.setItem("h1_profil", JSON.stringify(profil));
}

async function initFormulaireConnexion() {
  const form = document.getElementById("form-connexion");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const bouton = form.querySelector("button[type=submit]");
    bouton.disabled = true;
    bouton.textContent = "Connexion...";

    try {
      const donnees = {
        numero: form.numero.value.trim(),
        pin: form.pin.value.trim(),
      };
      const resultat = await Api.post("/api/auth/connexion", donnees);
      stockerSession(resultat.access_token, resultat.profil);
      window.location.href = "dashboard.html";
    } catch (err) {
      afficherErreurFormulaire(form, err.message);
      bouton.disabled = false;
      bouton.textContent = "Se connecter";
    }
  });
}

async function initFormulaireInscription() {
  const form = document.getElementById("form-inscription");
  if (!form) return;

  // Remplit dynamiquement la liste des options depuis l'API
  try {
    const options = await Api.get("/api/users/options");
    const select = form.option;
    options.forEach((o) => {
      const opt = document.createElement("option");
      opt.value = o.code;
      opt.textContent = `${o.nom} (${o.code})`;
      select.appendChild(opt);
    });
  } catch (_) {
    afficherToast("Impossible de charger la liste des options. Vérifiez que le serveur est démarré.", "erreur");
  }

  const inputPhoto = document.getElementById("photo");
  const apercu = document.getElementById("apercu-photo");
  let photoUrl = null;

  inputPhoto.addEventListener("change", async () => {
    const fichier = inputPhoto.files[0];
    if (!fichier) return;
    apercu.src = URL.createObjectURL(fichier);
    apercu.style.display = "block";

    try {
      const zoneStatut = document.getElementById("statut-upload");
      zoneStatut.textContent = "Envoi de la photo en cours...";
      const resultat = await Api.uploadPhoto(fichier);
      photoUrl = resultat.photo_url;
      zoneStatut.textContent = "Photo envoyée avec succès.";
      zoneStatut.style.color = "var(--succes)";
    } catch (err) {
      document.getElementById("statut-upload").textContent = "Échec de l'envoi : " + err.message;
      document.getElementById("statut-upload").style.color = "var(--erreur)";
    }
  });

  const compteurPresentation = document.getElementById("compteur-presentation");
  form.presentation.addEventListener("input", () => {
    compteurPresentation.textContent = `${form.presentation.value.length} / 800 caractères (minimum 50)`;
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    if (!photoUrl) {
      afficherToast("Merci d'attendre la fin de l'envoi de ta photo avant de valider.", "erreur");
      return;
    }

    const bouton = form.querySelector("button[type=submit]");
    bouton.disabled = true;
    bouton.textContent = "Envoi de la candidature...";

    const donnees = {
      photo_url: photoUrl,
      nom: form.nom.value.trim(),
      prenom: form.prenom.value.trim(),
      age: parseInt(form.age.value, 10),
      classe: form.classe.value.trim(),
      option: form.option.value,
      numero: form.numero.value.trim(),
      email: form.email.value.trim() || null,
      pin: form.pin.value.trim(),
      genre: form.genre.value,
      presentation: form.presentation.value.trim(),
      consentement_parental: form.consentement_parental.checked,
      charte_acceptee: form.charte_acceptee.checked,
    };

    try {
      const resultat = await Api.post("/api/auth/inscription", donnees);
      stockerSession(resultat.access_token, resultat.profil);
      window.location.href = "dashboard.html";
    } catch (err) {
      afficherErreurFormulaire(form, err.message);
      bouton.disabled = false;
      bouton.textContent = "Valider ma candidature";
    }
  });
}

function afficherErreurFormulaire(form, message) {
  let zone = form.querySelector(".alerte-formulaire");
  if (!zone) {
    zone = document.createElement("div");
    zone.className = "alerte-formulaire";
    zone.style.cssText = "background:#fdecea;color:#b71c1c;padding:12px 16px;border-radius:8px;margin-bottom:16px;font-size:0.88rem;";
    form.prepend(zone);
  }
  zone.textContent = message;
}

document.addEventListener("DOMContentLoaded", () => {
  initFormulaireConnexion();
  initFormulaireInscription();
});
