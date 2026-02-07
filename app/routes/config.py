import os
from datetime import timedelta

# Chemin du dossier de base
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Configuration générale de l'application."""

    # ── Sécurité ──────────────────────────────────
    # Valeur par défaut à changer en production
    SECRET_KEY = os.environ.get('SECRET_KEY', 'changez-cette-cle-en-production')

    # ── Base de données ───────────────────────────
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://localhost/anged_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Désactivation de la modification des notifications

    # ── Upload fichiers ───────────────────────────
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')  # Dossier d'upload des fichiers
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # Limite maximale de 5 MB pour les uploads

    # ── Session ───────────────────────────────────
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)  # Durée de vie de la session
    SESSION_COOKIE_HTTPONLY = True  # Protection contre les attaques XSS
    SESSION_COOKIE_SAMESITE = 'Lax'  # Politique de cookie SameSite

    # ── CSRF ──────────────────────────────────────
    WTF_CSRF_ENABLED = True  # Activation de la protection CSRF

    @staticmethod
    def validate():
        """Valide la configuration nécessaire à l'application."""
        if not Config.SECRET_KEY:
            raise ValueError("La clé secrète ('SECRET_KEY') doit être configurée.")
        if not Config.SQLALCHEMY_DATABASE_URI:
            raise ValueError("L'URI de base de données ('DATABASE_URL') doit être configurée.")
        # Ajoutez d'autres validations si nécessaire
