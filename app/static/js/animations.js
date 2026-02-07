// static/js/animations.js

// Classe pour l'animation au scroll
class ScrollAnimator {
  constructor() {
    this.elements = document.querySelectorAll("[data-animate]");
    this.init();
  }

  init() {
    const observer = new IntersectionObserver(this.onIntersect.bind(this), {
      threshold: 0.1,
      rootMargin: "0px 0px -50px 0px",
    });

    this.elements.forEach((el) => observer.observe(el));
  }

  onIntersect(entries) {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        this.animateElement(entry.target);
      }
    });
  }

  animateElement(element) {
    const animation = element.dataset.animate;
    const delay = parseInt(element.dataset.delay, 10) || 0;

    setTimeout(() => {
      element.classList.add(`animate-${animation}`);
      element.style.opacity = "1";
    }, delay);
  }
}

// Initialiser au chargement
document.addEventListener("DOMContentLoaded", () => {
  new ScrollAnimator();
});

// Fonction pour afficher un effet de confetti lors d'un succès
function showConfetti() {
  const confettiCount = 50;
  const colors = ["#ff0000", "#00ff00", "#0000ff", "#ffff00", "#ff00ff"];

  for (let i = 0; i < confettiCount; i++) {
    const confetti = createConfettiElement(colors);
    document.body.appendChild(confetti);

    setTimeout(() => confetti.remove(), 4000);
  }
}

// Création d'un élément confetti
function createConfettiElement(colors) {
  const confetti = document.createElement("div");
  confetti.className = "confetti";
  confetti.style.cssText = `
        position: fixed;
        width: 10px;
        height: 10px;
        background: ${colors[Math.floor(Math.random() * colors.length)]};
        left: ${Math.random() * 100}%;
        top: -10px;
        opacity: 1;
        transform: rotate(${Math.random() * 360}deg);
        animation: confetti-fall ${2 + Math.random() * 2}s linear;
    `;

  return confetti;
}

// Styles pour l'animation de confetti
const style = document.createElement("style");
style.textContent = `
    @keyframes confetti-fall {
        to {
            transform: translateY(100vh) rotate(${Math.random() * 720}deg);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Classe pour l'effet de particules
class ParticleEffect {
  constructor(container) {
    this.container = container;
    this.particles = [];
    this.createParticles();
  }

  createParticles() {
    for (let i = 0; i < 20; i++) {
      const particle = this.createParticle();
      this.container.appendChild(particle.element);
      this.particles.push(particle);
    }

    this.animate();
  }

  createParticle() {
    const particle = document.createElement("div");
    particle.className = "particle";
    particle.style.cssText = `
            position: absolute;
            width: ${Math.random() * 5 + 2}px;
            height: ${Math.random() * 5 + 2}px;
            background: rgba(255, 255, 255, 0.5);
            border-radius: 50%;
            pointer-events: none;
        `;

    return {
      element: particle,
      x: Math.random() * this.container.offsetWidth,
      y: Math.random() * this.container.offsetHeight,
      vx: (Math.random() - 0.5) * 2,
      vy: (Math.random() - 0.5) * 2,
    };
  }

  animate() {
    this.particles.forEach((p) => {
      p.x += p.vx;
      p.y += p.vy;

      if (p.x < 0 || p.x > this.container.offsetWidth) p.vx *= -1;
      if (p.y < 0 || p.y > this.container.offsetHeight) p.vy *= -1;

      p.element.style.left = `${p.x}px`;
      p.element.style.top = `${p.y}px`;
    });

    requestAnimationFrame(() => this.animate());
  }
}

// Fonction pour afficher un feedback visuel sur des actions
function showFeedback(element, type = "success") {
  const feedback = document.createElement("div");
  feedback.className = `feedback-${type}`;
  feedback.innerHTML = type === "success" ? "✓" : "✗";
  feedback.style.cssText = `
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        font-size: 48px;
        color: ${type === "success" ? "#10b981" : "#ef4444"};
        font-weight: bold;
        animation: feedback-pulse 0.6s ease-out;
        pointer-events: none;
        z-index: 9999;
    `;

  element.style.position = "relative";
  element.appendChild(feedback);

  setTimeout(() => feedback.remove(), 600);
}

// Styles pour le feedback visuel
const feedbackStyle = document.createElement("style");
feedbackStyle.textContent = `
    @keyframes feedback-pulse {
        0% {
            transform: translate(-50%, -50%) scale(0);
            opacity: 0;
        }
        50% {
            transform: translate(-50%, -50%) scale(1.2);
            opacity: 1;
        }
        100% {
            transform: translate(-50%, -50%) scale(1);
            opacity: 0;
        }
    }
`;
document.head.appendChild(feedbackStyle);
