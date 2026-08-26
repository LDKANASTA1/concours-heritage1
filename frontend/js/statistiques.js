/**
 * statistiques.js - alimente les pages statistiques.html et classement.html.
 * Utilise Chart.js (chargé via CDN dans les pages concernées).
 */

const COULEURS_OPTIONS = ["#667eea", "#764ba2", "#1a237e", "#2196f3", "#4caf50", "#ffd700", "#f44336"];

async function initStatistiquesGlobales() {
  const conteneurGraphique = document.getElementById("graphique-participation");
  if (!conteneurGraphique) return;

  try {
    const stats = await Api.get("/api/statistiques/globales");

    new Chart(conteneurGraphique, {
      type: "bar",
      data: {
        labels: stats.map((s) => s.option),
        datasets: [
          {
            label: "Votes exprimés",
            data: stats.map((s) => s.total_votes),
            backgroundColor: "#667eea",
            borderRadius: 6,
          },
          {
            label: "Inscrits",
            data: stats.map((s) => s.total_inscrits),
            backgroundColor: "#ffd700",
            borderRadius: 6,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: { legend: { position: "bottom" } },
        scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
      },
    });

    const grilleTaux = document.getElementById("grille-taux-participation");
    grilleTaux.innerHTML = stats.map((s) => `
      <div class="carte">
        <div class="flex-entre">
          <h3 style="margin:0;">${s.option}</h3>
          <span class="badge">${s.taux_participation}%</span>
        </div>
        <div class="ruban">
          <div class="ruban__piste"><div class="ruban__remplissage" style="width:${s.taux_participation}%"></div></div>
        </div>
        <p class="texte-att" style="margin:0;">${s.total_votants} votant(s) sur ${s.total_inscrits} inscrit(s)</p>
      </div>
    `).join("");
  } catch (err) {
    afficherToast("Impossible de charger les statistiques : " + err.message, "erreur");
  }
}

async function initClassementOption() {
  const conteneur = document.getElementById("classement-option");
  if (!conteneur) return;

  const params = new URLSearchParams(window.location.search);
  const option = params.get("option") || "MG";
  document.querySelectorAll(".selecteur-option").forEach((btn) => {
    btn.classList.toggle("actif", btn.dataset.option === option);
  });

  try {
    const classement = await Api.get(`/api/statistiques/classement/${option}`);
    const totalVotes = classement.reduce((acc, e) => acc + e.nb_votes, 0) || 1;

    conteneur.innerHTML = classement.map((entree) => {
      const pourcentage = Math.round((entree.nb_votes / totalVotes) * 100);
      const estPremier = entree.position === 1 && entree.nb_votes > 0;
      return `
        <div class="carte flex" style="margin-bottom:14px; align-items:center;">
          <span class="badge ${estPremier ? "badge--or anim-en-tete" : ""}" style="min-width:32px; text-align:center;">${entree.position}</span>
          <img src="${entree.candidat.photo_url}" alt="${entree.candidat.prenom}" style="width:54px;height:54px;border-radius:50%;object-fit:cover;" loading="lazy">
          <div style="flex:1;">
            <strong>${entree.candidat.prenom} ${entree.candidat.nom}</strong>
            <div class="ruban">
              <div class="ruban__piste"><div class="ruban__remplissage ${estPremier ? "est-premier" : ""}" style="width:${pourcentage}%"></div></div>
              <span class="ruban__valeur">${entree.nb_votes}</span>
            </div>
          </div>
        </div>`;
    }).join("") || `<div class="vide"><i class="fa-solid fa-inbox"></i><p>Aucun candidat pour cette option.</p></div>`;
  } catch (err) {
    conteneur.innerHTML = `<div class="vide"><p>${err.message}</p></div>`;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initStatistiquesGlobales();
  initClassementOption();
});
