/**
 * votes.js - vote direct, sans duel : l'utilisateur choisit un candidat dans une liste
 * et confirme son choix. Le vote peut être modifié tant que la phase reste ouverte.
 */

function profilConnecte() {
  const brut = localStorage.getItem("h1_profil");
  return brut ? JSON.parse(brut) : null;
}

async function initVoteOption() {
  const conteneur = document.getElementById("liste-candidats-option");
  if (!conteneur) return;

  const profil = profilConnecte();
  document.getElementById("nom-option-vote").textContent = profil.option;

  let candidatChoisiId = null;

  try {
    const [candidats, monVote] = await Promise.all([
      Api.get(`/api/users/candidats/${profil.option}`),
      Api.get(`/api/votes/mon-vote/option`),
    ]);

    if (monVote) candidatChoisiId = monVote.candidat_id;

    conteneur.innerHTML = candidats
      .filter((c) => c.id !== profil.id)
      .map((c) => carteCandidatVote(c, candidatChoisiId === c.id))
      .join("");

    if (candidats.filter((c) => c.id !== profil.id).length === 0) {
      conteneur.innerHTML = `<div class="vide"><i class="fa-solid fa-user-group"></i><p>Aucun autre candidat n'est encore inscrit dans ton option.</p></div>`;
    }

    attacherEcouteursVote(conteneur, "option", () => {
      document.getElementById("etat-vote-option").textContent = "Vote enregistré. Tu peux le modifier à tout moment tant que le vote est ouvert.";
    });
  } catch (err) {
    conteneur.innerHTML = `<div class="vide"><i class="fa-solid fa-triangle-exclamation"></i><p>${err.message}</p></div>`;
  }
}

async function initVoteFinale() {
  const conteneur = document.getElementById("liste-candidats-finale");
  if (!conteneur) return;

  const profil = profilConnecte();
  let candidatChoisiId = null;

  try {
    const [candidats, monVote] = await Promise.all([
      Api.get("/api/votes/candidats-finale"),
      Api.get("/api/votes/mon-vote/finale"),
    ]);

    if (monVote) candidatChoisiId = monVote.candidat_id;

    if (!candidats.length) {
      conteneur.innerHTML = `<div class="vide"><i class="fa-solid fa-hourglass-half"></i><p>La finale n'est pas encore ouverte : les 7 ambassadeurs d'options doivent d'abord être désignés.</p></div>`;
      return;
    }

    conteneur.innerHTML = candidats
      .filter((c) => c.id !== profil.id)
      .map((c) => carteCandidatVote(c, candidatChoisiId === c.id, true))
      .join("");

    attacherEcouteursVote(conteneur, "finale", () => {
      document.getElementById("etat-vote-finale").textContent = "Vote enregistré pour le Grand Ambassadeur de la Promotion.";
    });
  } catch (err) {
    conteneur.innerHTML = `<div class="vide"><i class="fa-solid fa-triangle-exclamation"></i><p>${err.message}</p></div>`;
  }
}

function carteCandidatVote(candidat, selectionne, afficherOption = false) {
  return `
    <div class="carte carte--candidat anim-entree" data-candidat-id="${candidat.id}">
      <img class="carte--candidat__photo" src="${candidat.photo_url}" alt="Photo de ${candidat.prenom} ${candidat.nom}" loading="lazy">
      <div class="carte--candidat__corps">
        ${afficherOption ? `<span class="badge">${candidat.option}</span>` : ""}
        <h3 style="margin-top:8px;">${candidat.prenom} ${candidat.nom}</h3>
        <p class="texte-att" style="flex:1;">${candidat.presentation.slice(0, 140)}${candidat.presentation.length > 140 ? "…" : ""}</p>
        <button class="bouton ${selectionne ? "bouton--or" : "bouton--principal"} bouton--bloc bouton-voter" data-id="${candidat.id}">
          <i class="fa-solid ${selectionne ? "fa-check" : "fa-hand-point-up"}"></i>
          ${selectionne ? "Ton candidat actuel" : "Voter pour ce candidat"}
        </button>
      </div>
    </div>`;
}

function attacherEcouteursVote(conteneur, phase, callbackSucces) {
  conteneur.querySelectorAll(".bouton-voter").forEach((bouton) => {
    bouton.addEventListener("click", async () => {
      const candidatId = parseInt(bouton.dataset.id, 10);
      bouton.disabled = true;
      const texteOriginal = bouton.innerHTML;
      bouton.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Envoi...`;

      try {
        await Api.post("/api/votes", { candidat_id: candidatId, phase });
        afficherToast("Ton vote a bien été pris en compte.", "succes");
        callbackSucces();
        // Réactualise l'affichage pour marquer le nouveau choix
        conteneur.querySelectorAll(".bouton-voter").forEach((b) => {
          const estCelui = parseInt(b.dataset.id, 10) === candidatId;
          b.classList.toggle("bouton--or", estCelui);
          b.classList.toggle("bouton--principal", !estCelui);
          b.innerHTML = estCelui
            ? `<i class="fa-solid fa-check"></i> Ton candidat actuel`
            : `<i class="fa-solid fa-hand-point-up"></i> Voter pour ce candidat`;
          b.disabled = false;
        });
      } catch (err) {
        afficherToast(err.message, "erreur");
        bouton.innerHTML = texteOriginal;
        bouton.disabled = false;
      }
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initVoteOption();
  initVoteFinale();
});
