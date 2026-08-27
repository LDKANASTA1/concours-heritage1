/**
 * share.js - branche les boutons de partage WhatsApp présents sur les pages de statistiques.
 * Le message est généré côté serveur (voir /api/share/message/{type_page}) pour rester cohérent partout.
 */

async function brancherPartage(selecteur, typePage, detail = "") {
  const boutons = document.querySelectorAll(selecteur);
  if (!boutons.length) return;

  boutons.forEach((bouton) => {
    bouton.addEventListener("click", async () => {
      try {
        const { lien_whatsapp } = await Api.get(`/api/share/message/${typePage}?detail=${encodeURIComponent(detail)}`);
        await Api.post("/api/share", {
          type_partage: "whatsapp",
          page_partagee: typePage,
          url_partage: window.location.href,
        });
        window.open(lien_whatsapp, "_blank", "noopener");
      } catch (err) {
        afficherToast("Impossible de préparer le partage : " + err.message, "erreur");
      }
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  brancherPartage("[data-partage='accueil']", "accueil");
  brancherPartage("[data-partage='classement']", "classement");
  brancherPartage("[data-partage='finale']", "finale");

  document.querySelectorAll("[data-partage='option']").forEach((bouton) => {
    bouton.addEventListener("click", async () => {
      const option = bouton.dataset.optionCode || "";
      try {
        const { lien_whatsapp } = await Api.get(`/api/share/message/option?detail=${encodeURIComponent(option)}`);
        window.open(lien_whatsapp, "_blank", "noopener");
      } catch (err) {
        afficherToast(err.message, "erreur");
      }
    });
  });
});
