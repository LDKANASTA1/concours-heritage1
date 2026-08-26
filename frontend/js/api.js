/**
 * Client API - point d'entrée unique vers le backend FastAPI.
 * Modifiez API_BASE_URL selon votre environnement (voir .env du frontend / README).
 */
const API_BASE_URL = window.HERITAGE1_API_URL || "http://localhost:8000";

const Api = {
  _token() {
    return localStorage.getItem("h1_token");
  },

  async _requete(chemin, options = {}) {
    const entetes = { ...(options.headers || {}) };
    if (!(options.body instanceof FormData)) {
      entetes["Content-Type"] = "application/json";
    }
    const token = this._token();
    if (token) entetes["Authorization"] = `Bearer ${token}`;

    const reponse = await fetch(`${API_BASE_URL}${chemin}`, { ...options, headers: entetes });

    if (reponse.status === 204) return null;

    let corps = null;
    try { corps = await reponse.json(); } catch (_) { /* pas de corps JSON */ }

    if (!reponse.ok) {
      const message = corps?.detail || "Une erreur est survenue. Réessayez.";
      throw new Error(typeof message === "string" ? message : JSON.stringify(message));
    }
    return corps;
  },

  get(chemin) { return this._requete(chemin, { method: "GET" }); },
  post(chemin, donnees) { return this._requete(chemin, { method: "POST", body: JSON.stringify(donnees) }); },
  patch(chemin, donnees) { return this._requete(chemin, { method: "PATCH", body: JSON.stringify(donnees) }); },
  del(chemin) { return this._requete(chemin, { method: "DELETE" }); },

  async uploadPhoto(fichier) {
    const formData = new FormData();
    formData.append("fichier", fichier);
    return this._requete("/api/users/upload-photo", { method: "POST", body: formData });
  },
};
