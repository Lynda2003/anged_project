from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from .config import Config

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialiser extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Configuration Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter.'

    # Enregistrer blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.cahier import cahier_bp
    from app.routes.depot import depot_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(cahier_bp)
    app.register_blueprint(depot_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(cahier_bp)
    app.register_blueprint(depot_bp)
    app.register_blueprint(admin_bp)

    return app
