/**
 * app.js - initialisation commune à toutes les pages :
 * navigation (avec état connecté/déconnecté), menu hamburger, toasts, pied de page.
 */

const NOM_ECOLE = "Complexe Scolaire HERITAGE 1";
const WHATSAPP_SUPPORT = "https://wa.me/243826740490";
const EMAIL_SUPPORT = "ldkanasta@gmail.com";

function estConnecte() {
  return !!localStorage.getItem("h1_token");
}

function deconnecter() {
  localStorage.removeItem("h1_token");
  localStorage.removeItem("h1_profil");
  window.location.href = calculerRacine() + "index.html";
}

/** Calcule le préfixe relatif ("" à la racine, "../" dans /pages/) pour que les liens marchent partout. */
function calculerRacine() {
  return window.location.pathname.includes("/pages/") ? "../" : "";
}

function construireNav() {
  const racine = calculerRacine();
  const connecte = estConnecte();
  const page = window.location.pathname.split("/").pop();

  const liensPublics = [
    ["index.html", "Accueil"],
    ["pages/options.html", "Options"],
    ["pages/classement.html", "Classement"],
    ["pages/statistiques.html", "Statistiques"],
    ["pages/reglements.html", "Règlement"],
    ["pages/contact.html", "Contact"],
  ];

  const liensHtml = liensPublics.map(([chemin, libelle]) => {
    const cible = racine + chemin;
    const nomFichier = chemin.split("/").pop();
    const actif = page === nomFichier ? " actif" : "";
    return `<a href="${cible}" class="${actif.trim()}">${libelle}</a>`;
  }).join("");

  const actionsHtml = connecte
    ? `<a href="${racine}pages/notifications.html" class="bouton bouton--petit bouton--contour" style="color:#fff;border-color:rgba(255,255,255,0.5);"><i class="fa-solid fa-bell"></i></a>
       <a href="${racine}pages/dashboard.html" class="bouton bouton--petit bouton--or">Mon espace</a>`
    : `<a href="${racine}pages/login.html" class="bouton bouton--petit bouton--contour" style="color:#fff;border-color:rgba(255,255,255,0.5);">Connexion</a>
       <a href="${racine}pages/inscription.html" class="bouton bouton--petit bouton--or">S'inscrire</a>`;

  return `
    <header class="entete">
      <nav class="nav">
        <a href="${racine}index.html" class="nav__marque">
          <i class="fa-solid fa-award"></i> ${NOM_ECOLE}
        </a>
        <ul class="nav__liens" id="nav-liens">${liensHtml}</ul>
        <div class="nav__actions">
          ${actionsHtml}
          <button class="nav__burger" id="nav-burger" aria-label="Ouvrir le menu"><i class="fa-solid fa-bars"></i></button>
        </div>
      </nav>
    </header>`;
}

function construirePied() {
  const racine = calculerRacine();
  return `
    <footer class="pied">
      <div class="conteneur">
        <div class="pied__grille">
          <div>
            <h4>${NOM_ECOLE}</h4>
            <p style="color:rgba(255,255,255,0.65); font-size:0.88rem;">
              Concours des Ambassadeurs de la Promotion - 6e des humanités.
              Un vote direct, transparent et vérifiable par toute la promotion.
            </p>
          </div>
          <div>
            <h4>Navigation</h4>
            <ul>
              <li><a href="${racine}pages/options.html">Les 7 options</a></li>
              <li><a href="${racine}pages/classement.html">Classement</a></li>
              <li><a href="${racine}pages/reglements.html">Règlement du concours</a></li>
              <li><a href="${racine}pages/mentions.html">Mentions légales</a></li>
            </ul>
          </div>
          <div>
            <h4>Support</h4>
            <ul>
              <li><i class="fa-solid fa-envelope"></i> <a href="mailto:${EMAIL_SUPPORT}">${EMAIL_SUPPORT}</a></li>
              <li><i class="fa-brands fa-whatsapp"></i> <a href="${WHATSAPP_SUPPORT}" target="_blank" rel="noopener">+243 826 740 490</a></li>
              <li><a href="${racine}pages/contact.html">Formulaire de contact</a></li>
            </ul>
          </div>
        </div>
        <div class="pied__bas">
          <span>&copy; ${new Date().getFullYear()} ${NOM_ECOLE} - République Démocratique du Congo</span>
          <span><i class="fa-solid fa-eye"></i> <span id="compteur-visites">...</span> visite(s) depuis le lancement</span>
        </div>
      </div>
    </footer>
    <a href="${WHATSAPP_SUPPORT}" target="_blank" rel="noopener" class="whatsapp-flottant" aria-label="Contacter le support par WhatsApp">
      <i class="fa-brands fa-whatsapp"></i>
    </a>
    <div class="zone-toasts" id="zone-toasts"></div>`;
}

/**
 * Compteur de visiteurs : incrémente une seule fois par session de navigateur
 * (sessionStorage), puis affiche le total dans le pied de page sur chaque page.
 */
async function initialiserCompteurVisites() {
  const zoneAffichage = document.getElementById("compteur-visites");
  if (!zoneAffichage) return;

  try {
    let resultat;
    if (!sessionStorage.getItem("h1_visite_comptee")) {
      resultat = await Api.post("/api/visites/incrementer", {});
      sessionStorage.setItem("h1_visite_comptee", "1");
    } else {
      resultat = await Api.get("/api/visites");
    }
    zoneAffichage.textContent = resultat.total_visites.toLocaleString("fr-FR");
  } catch (_) {
    zoneAffichage.textContent = "—";
  }
}

function afficherToast(message, type = "info") {
  const zone = document.getElementById("zone-toasts");
  if (!zone) return;
  const toast = document.createElement("div");
  toast.className = `toast toast--${type}`;
  toast.textContent = message;
  zone.appendChild(toast);
  setTimeout(() => toast.remove(), 4500);
}

function initialiserApp() {
  const enteteRacine = document.getElementById("entete-racine");
  const piedRacine = document.getElementById("pied-racine");
  if (enteteRacine) enteteRacine.innerHTML = construireNav();
  if (piedRacine) piedRacine.innerHTML = construirePied();
  initialiserCompteurVisites();

  const burger = document.getElementById("nav-burger");
  const liens = document.getElementById("nav-liens");
  if (burger && liens) {
    burger.addEventListener("click", () => liens.classList.toggle("ouvert"));
  }

  // Protection simple des pages privées : redirige vers la connexion si non connecté
  const pagesProtegees = ["dashboard.html", "vote-option.html", "vote-finale.html", "profil.html", "notifications.html"];
  const pageActuelle = window.location.pathname.split("/").pop();
  if (pagesProtegees.includes(pageActuelle) && !estConnecte()) {
    window.location.href = "login.html";
  }
}

document.addEventListener("DOMContentLoaded", initialiserApp);
