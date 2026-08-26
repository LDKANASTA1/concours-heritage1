/**
 * notifications.js - centre de notifications de l'élève connecté.
 */

const ICONES_NOTIF = {
  vote: "fa-check-to-slot",
  elu: "fa-trophy",
  systeme: "fa-gear",
  info: "fa-circle-info",
  moderation: "fa-shield-halved",
};

async function initNotifications() {
  const conteneur = document.getElementById("liste-notifications");
  if (!conteneur) return;

  try {
    const notifications = await Api.get("/api/notifications");

    if (!notifications.length) {
      conteneur.innerHTML = `<div class="vide"><i class="fa-solid fa-bell-slash"></i><p>Aucune notification pour le moment.</p></div>`;
      return;
    }

    conteneur.innerHTML = notifications.map((n) => `
      <div class="carte flex ${n.est_lu ? "" : "anim-entree"}" style="margin-bottom:12px; align-items:flex-start; ${n.est_lu ? "opacity:0.6;" : "border-left:4px solid var(--degrade-fin);"}" data-id="${n.id}">
        <i class="fa-solid ${ICONES_NOTIF[n.type] || "fa-circle-info"}" style="font-size:1.3rem; color: var(--degrade-fin); margin-top:4px;"></i>
        <div style="flex:1;">
          <strong>${n.titre}</strong>
          <p style="margin:4px 0 0;">${n.message}</p>
          <span class="texte-att">${new Date(n.date_creation).toLocaleString("fr-FR")}</span>
        </div>
        ${n.est_lu ? "" : `<button class="bouton bouton--petit bouton--contour marquer-lu" data-id="${n.id}">Marquer comme lu</button>`}
      </div>
    `).join("");

    conteneur.querySelectorAll(".marquer-lu").forEach((bouton) => {
      bouton.addEventListener("click", async () => {
        try {
          await Api.patch(`/api/notifications/${bouton.dataset.id}/lu`, {});
          initNotifications();
        } catch (err) {
          afficherToast(err.message, "erreur");
        }
      });
    });

    const boutonTout = document.getElementById("marquer-tout-lu");
    if (boutonTout) {
      boutonTout.onclick = async () => {
        await Api.post("/api/notifications/tout-marquer-lu", {});
        initNotifications();
      };
    }
  } catch (err) {
    conteneur.innerHTML = `<div class="vide"><p>${err.message}</p></div>`;
  }
}

document.addEventListener("DOMContentLoaded", initNotifications);
