// static/js/htmx-config.js

// Configuration globale HTMX
document.body.addEventListener("htmx:configRequest", (evt) => {
  // Ajouter le CSRF token à toutes les requêtes
  evt.detail.headers["X-CSRFToken"] = getCsrfToken();
});

// Fonction pour créer et ajouter un spinner
function createSpinner(target) {
  const spinner = document.createElement("div");
  spinner.className = "loading-spinner";
  spinner.id = "htmx-spinner";
  target.appendChild(spinner);
}

// Animations avant requête
document.body.addEventListener("htmx:beforeRequest", (evt) => {
  const target = evt.detail.target;

  // Éléments de chargement
  target.classList.add("htmx-loading");
  createSpinner(target);

  // Animation de transition
  target.style.transition = "opacity 0.3s";
  target.style.opacity = "0.5";
});

// Animations après requête
document.body.addEventListener("htmx:afterRequest", (evt) => {
  const target = evt.detail.target;

  // Retirer classe de chargement et spinner
  target.classList.remove("htmx-loading");
  const spinner = document.getElementById("htmx-spinner");
  if (spinner) {
    spinner.remove();
  }

  // Rétablir l'opacité
  target.style.opacity = "1";
  target.classList.add("animate-fade-in");
});

// Gestion des erreurs
document.body.addEventListener("htmx:responseError", () => {
  showNotification("Erreur lors du chargement", "error");
});

// Gestion des succès
document.body.addEventListener("htmx:afterSwap", (evt) => {
  // Réinitialiser les animations des éléments
  evt.detail.target.querySelectorAll(".animate-on-load").forEach((el) => {
    el.classList.add("animate-fade-in");
  });
});

// Fonction utilitaire pour obtenir le token CSRF
function getCsrfToken() {
  const tokenMeta = document.querySelector('meta[name="csrf-token"]');
  return tokenMeta ? tokenMeta.getAttribute("content") : "";
}

// Système de notification
function showNotification(message, type = "info") {
  const notification = document.createElement("div");
  notification.className = `
        fixed top-4 right-4 z-50 px-6 py-4 rounded-lg shadow-2xl
        animate-slide-in-right
        ${getNotificationClass(type)}
        text-white font-semibold
    `;

  notification.innerHTML = `
        <div class="flex items-center space-x-3">
            <i class="${getNotificationIcon(type)} text-2xl"></i>
            <span>${message}</span>
        </div>
    `;

  document.body.appendChild(notification);

  // Animation de sortie après 3 secondes
  setTimeout(() => {
    notification.classList.add("animate-slide-out-right");
    setTimeout(() => notification.remove(), 500);
  }, 3000);
}

// Fonction utilitaire pour obtenir la classe de notification en fonction du type
function getNotificationClass(type) {
  switch (type) {
    case "success":
      return "bg-green-500";
    case "error":
      return "bg-red-500";
    case "warning":
      return "bg-orange-500";
    default:
      return "bg-blue-500";
  }
}

// Fonction utilitaire pour obtenir l'icône de notification en fonction du type
function getNotificationIcon(type) {
  switch (type) {
    case "success":
      return "fas fa-check-circle";
    case "error":
      return "fas fa-times-circle";
    case "warning":
      return "fas fa-exclamation-circle";
    default:
      return "fas fa-info-circle";
  }
}
