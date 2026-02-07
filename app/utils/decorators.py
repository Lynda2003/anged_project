"""
Décorateurs personnalisés pour l'application
"""

from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user


def admin_required(f):
    """
    Décorateur pour vérifier si l'utilisateur est administrateur.

    Usage:
        @admin_bp.route('/dashboard')
        @login_required
        @admin_required
        def dashboard():
            # Code ici
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Vérifier si l'utilisateur est connecté
        if not current_user.is_authenticated:
            flash('Veuillez vous connecter.', 'warning')
            return redirect(url_for('auth.login'))

        # Vérifier si l'utilisateur a le rôle d'admin
        if not current_user.is_admin():
            flash('Accès réservé aux administrateurs.', 'danger')
            return redirect(url_for('main.dashboard'))

        return f(*args, **kwargs)  # Appel de la fonction décorée

    return decorated_function


def role_required(role):
    """
    Décorateur générique pour vérifier le rôle de l'utilisateur.

    Usage:
        @role_required('admin')
        def admin_function():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Vérifier si l'utilisateur est connecté
            if not current_user.is_authenticated:
                flash('Veuillez vous connecter.', 'warning')
                return redirect(url_for('auth.login'))

            # Vérifier si l'utilisateur a le rôle requis
            if current_user.role != role:
                flash('Accès interdit. Vous n\'avez pas les permissions requises.', 'danger')
                abort(403)  # Interdiction d'accès

            return f(*args, **kwargs)  # Appel de la fonction décorée

        return decorated_function
    return decorator
