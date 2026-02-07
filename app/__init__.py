from app.routes.main import main_bp
from app.routes.admin import admin_bp
from app.routes.depot import depot_bp
from app.routes.cahier import cahier_bp
from app.routes.auth import auth_bp
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

# ============================================
# INSTANCE DES EXTENSIONS (déclarées globalement)
# ============================================
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()
csrf = CSRFProtect()

# ============================================
# IMPORT DES BLUEPRINTS
# ============================================

# ============================================
# FONCTION DE CRÉATION DE L'APPLICATION
# ============================================


def create_app(config_class=None):
    """
    Factory Pattern : Crée et configure l'application Flask

    Args:
        config_class: Classe de configuration (par défaut: app.config.Config)

    Returns:
        app: Instance de l'application Flask configurée
    """

    # ============================================
    # CRÉATION DE L'APPLICATION
    # ============================================
    app = Flask(__name__, template_folder='templates', static_folder='static')

    # ============================================
    # CONFIGURATION
    # ============================================
    if config_class is None:
        from app.config import Config
        app.config.from_object(Config)
    else:
        app.config.from_object(config_class)

    # ============================================
    # INITIALISATION DES EXTENSIONS
    # ============================================
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # ============================================
    # CONFIGURATION DU LOGIN MANAGER
    # ============================================
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        """Charge un utilisateur depuis la base de données"""
        from app.models.user import User  # Import interne pour éviter des boucles
        return User.query.get(int(user_id))

    # ============================================
    # IMPORT ET ENREGISTREMENT DES MODELS
    # ============================================
    from app.models.user import User
    from app.models.cahier import CahierDeCharge
    from app.models.depot import Depot
    from app.models.suivi import Suivi

    # ============================================
    # ENREGISTREMENT DES BLUEPRINTS
    # ============================================
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(cahier_bp, url_prefix='/cahier')
    app.register_blueprint(depot_bp, url_prefix='/depot')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # ============================================
    # CONTEXT PROCESSORS (Variables globales dans les templates)
    # ============================================
    @app.context_processor
    def inject_user():
        """Injecte l'utilisateur courant dans tous les templates"""
        from flask_login import current_user
        return dict(current_user=current_user)

    @app.context_processor
    def inject_notifications():
        """Injecte les notifications dans tous les templates"""
        from flask_login import current_user
        from app.models.suivi import Suivi

        if current_user.is_authenticated and current_user.role == 'admin':
            documents_en_attente = Suivi.query.filter_by(statut='en_attente').count()
            return dict(notifications_count=documents_en_attente)
        return dict(notifications_count=0)

    # ============================================
    # FILTRES JINJA PERSONNALISÉS
    # ============================================
    @app.template_filter('datetime_fr')
    def datetime_fr_filter(value, format='%d/%m/%Y %H:%M'):
        """Formatte une date au format français"""
        if value is None:
            return ''
        return value.strftime(format)

    @app.template_filter('statut_badge')
    def statut_badge_filter(statut):
        """Retourne la classe CSS pour un badge de statut"""
        badges = {
            'vert': 'bg-green-100 text-green-800',
            'orange': 'bg-orange-100 text-orange-800',
            'rouge': 'bg-red-100 text-red-800',
            'en_attente': 'bg-yellow-100 text-yellow-800',
            'valide': 'bg-green-100 text-green-800',
            'refuse': 'bg-red-100 text-red-800'
        }
        return badges.get(statut, 'bg-gray-100 text-gray-800')

    # ============================================
    # GESTION DES ERREURS
    # ============================================
    @app.errorhandler(404)
    def page_not_found(e):
        """Gestion de l'erreur 404 (Page non trouvée)"""
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        """Gestion de l'erreur 403 (Accès interdit)"""
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_server_error(e):
        """Gestion de l'erreur 500 (Erreur serveur)"""
        db.session.rollback()  # Annule toute transaction en cours
        return render_template('errors/500.html'), 500

    # ============================================
    # COMMANDES CLI PERSONNALISÉES
    # ============================================
    @app.cli.command('init-db')
    def init_db_command():
        """Initialise la base de données (création des tables)"""
        db.create_all()
        print('Base de données initialisée avec succès !')

    @app.cli.command('seed-db')
    def seed_db_command():
        """Remplit la base de données avec des données de test"""
        from app.models.user import User

        if not User.query.filter_by(email='admin@anged.ma').first():
            admin = User(
                email='admin@anged.ma',
                prenom='Admin',
                nom='ANGED',
                role='admin'
            )
            admin.set_password('admin123')  # Méthode à implémenter dans le modèle User

            db.session.add(admin)
            db.session.commit()
            print('Données de test ajoutées avec succès !')
        else:
            print('Un utilisateur admin existe déjà dans la base de données.')

    # ============================================
    # FONCTION DE NETTOYAGE AVANT CHAQUE REQUÊTE
    # ============================================
    @app.before_request
    def before_request():
        """Actions à effectuer avant chaque requête"""
        pass  # Vous pouvez ajouter des logs, vérifications, etc.

    # ============================================
    # FONCTION APRÈS CHAQUE REQUÊTE
    # ============================================
    @app.after_request
    def after_request(response):
        """Actions à effectuer après chaque requête"""
        # Ajoute des headers de sécurité
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response

    # ============================================
    # RETOUR DE L'APPLICATION
    # ============================================
    return app
