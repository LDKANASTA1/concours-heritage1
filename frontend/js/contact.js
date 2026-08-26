/**
 * contact.js - formulaire de contact public.
 */

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("form-contact");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const bouton = form.querySelector("button[type=submit]");
    bouton.disabled = true;
    bouton.textContent = "Envoi en cours...";

    try {
      await Api.post("/api/contact", {
        nom: form.nom.value.trim(),
        email: form.email.value.trim(),
        telephone: form.telephone.value.trim() || null,
        sujet: form.sujet.value.trim(),
        message: form.message.value.trim(),
      });
      afficherToast("Message envoyé ! Une confirmation t'a été envoyée par email.", "succes");
      form.reset();
    } catch (err) {
      afficherToast(err.message, "erreur");
    } finally {
      bouton.disabled = false;
      bouton.textContent = "Envoyer le message";
    }
  });
});
