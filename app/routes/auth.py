from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User
from werkzeug.security import check_password_hash
import itsdangerous
from flask_mail import Mail, Message

# Création du blueprint — nom EXACTEMENT "auth_bp"
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Configuration de Flask-Mail
mail = Mail()

# ============================================================
# PAGE LOGIN
# ============================================================


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Si déjà connecté → rediriger vers dashboard
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Chercher l'utilisateur
        user = User.query.filter_by(email=email).first()

        # Vérifier email et mot de passe
        if user and check_password_hash(user.password_hash, password):
            if not user.actif:
                flash('Votre compte est désactivé.', 'danger')
                return redirect(url_for('auth.login'))

            login_user(user)
            flash(f'Bienvenue, {user.prenom} !', 'success')

            # Rediriger vers admin si admin, sinon dashboard
            if user.is_admin():
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('main.dashboard'))
        else:
            flash('Email ou mot de passe incorrect.', 'danger')

    return render_template('auth/login.html')


# ============================================================
# LOGOUT
# ============================================================
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('auth.login'))


# ============================================================
# RÉINITIALISER MOT DE PASSE
# ============================================================
@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()

        if user:
            token = generate_reset_token(user.email)
            send_password_reset_email(user.email, token)
            flash('Un email a été envoyé avec les instructions pour réinitialiser votre mot de passe.', 'success')
        else:
            flash('Email non trouvé.', 'danger')

        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html')


def generate_reset_token(email, expiration=3600):
    s = itsdangerous.URLSafeTimedSerializer('votre_signature_secrète')  # Remplacez par votre clé secrète
    return s.dumps(email, salt='reset-password-salt')


def send_password_reset_email(email, token):
    link = url_for("auth.reset_with_token", token=token, _external=True)
    msg = Message(
        'Réinitialisation du mot de passe',
        sender='votre-email@example.com',  # Remplacez par votre adresse email
        recipients=[email]
    )
    msg.body = (
        'Cliquez sur le lien pour réinitialiser votre mot de passe : '
        f'{link}'
    )
    mail.send(msg)


@auth_bp.route('/reset-with-token/<token>', methods=['GET', 'POST'])
def reset_with_token(token):
    s = itsdangerous.URLSafeTimedSerializer('votre_signature_secrète')  # Remplacez par votre clé secrète
    try:
        email = s.loads(token, salt='reset-password-salt', max_age=3600)
    except itsdangerous.SignatureExpired:
        flash('Le lien a expiré.', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        new_password = request.form.get('new_password')
        user = User.query.filter_by(email=email).first()
        if user:
            user.set_password(new_password)  # Vous devez avoir une méthode set_password dans votre modèle Utilisateur
            db.session.commit()
            flash('Votre mot de passe a été réinitialisé avec succès.', 'success')
            return redirect(url_for('auth.login'))

    return render_template('auth/reset_with_token.html', token=token)
