from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models.cahier import CahierCharge
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)

# Création du blueprint — nom EXACTEMENT "cahier_bp"
cahier_bp = Blueprint('cahier', __name__, url_prefix='/cahiers')

# ============================================================
# LISTE DES CAHIERS (avec filtrage HTMX)
# ============================================================


@cahier_bp.route('/list')
@login_required
def list_cahiers():
    type_cahier = request.args.get('type', 'all')
    page = request.args.get('page', 1, type=int)

    # Requête de base
    query = CahierCharge.query.filter_by(user_id=current_user.id)

    # Filtrer par type
    if type_cahier != 'all':
        query = query.filter_by(type=type_cahier)

    # Ordonner par date (plus récent en premier)
    query = query.order_by(CahierCharge.created_at.desc())

    # Pagination
    cahiers = query.paginate(page=page, per_page=9, error_out=False)

    # Si requête HTMX → renvoyer seulement les items
    if request.headers.get('HX-Request'):
        return render_template('cahier/_cahier_list_items.html', cahiers=cahiers.items)

    # Sinon → page complète
    return render_template('cahier/list.html',
                           cahiers=cahiers.items,
                           has_next=cahiers.has_next,
                           next_page=cahiers.next_num if cahiers.has_next else None,
                           type_filter=type_cahier)


# ============================================================
# CRÉER UN CAHIER
# ============================================================
@cahier_bp.route('/create/<type_cahier>', methods=['GET', 'POST'])
@login_required
def create(type_cahier):
    if type_cahier not in ['recyclage', 'stockage']:
        flash('Type de cahier invalide.', 'danger')
        return redirect(url_for('cahier.list_cahiers'))

    if request.method == 'POST':
        titre = request.form.get('titre', '').strip()
        nom_entreprise = request.form.get('nom_entreprise', '').strip()

        # Créer le cahier
        cahier = CahierCharge(
            user_id=current_user.id,
            type=type_cahier,
            titre=titre,
            nom_entreprise=nom_entreprise,
            donnees_formulaire=request.form.to_dict(),
            statut='brouillon'
        )

        try:
            db.session.add(cahier)
            db.session.commit()
            flash(f'Cahier de charge {type_cahier} créé avec succès !', 'success')
            return redirect(url_for('cahier.list_cahiers'))
        except Exception as e:
            db.session.rollback()  # Annuler la transaction en cas d'erreur
            logging.error(f"Erreur lors de la création du cahier: {e}")  # Journaliser l'erreur
            flash('Erreur lors de la création du cahier. Veuillez réessayer.', 'danger')

    # Afficher le formulaire
    template = f'cahier/{type_cahier}.html'
    return render_template(template, mode='create')


# ============================================================
# VOIR UN CAHIER
# ============================================================
@cahier_bp.route('/view/<int:cahier_id>')
@login_required
def view(cahier_id):
    cahier = CahierCharge.query.get_or_404(cahier_id)

    # Vérifier que c'est bien le propriétaire
    if cahier.user_id != current_user.id:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('cahier.list_cahiers'))

    return render_template('cahier/view.html', cahier=cahier)


# ============================================================
# MODIFIER UN CAHIER
# ============================================================
@cahier_bp.route('/edit/<int:cahier_id>', methods=['GET', 'POST'])
@login_required
def edit(cahier_id):
    cahier = CahierCharge.query.get_or_404(cahier_id)

    if cahier.user_id != current_user.id:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('cahier.list_cahiers'))

    if request.method == 'POST':
        cahier.titre = request.form.get('titre', cahier.titre).strip()
        cahier.nom_entreprise = request.form.get('nom_entreprise', cahier.nom_entreprise).strip()
        cahier.donnees_formulaire = request.form.to_dict()

        try:
            db.session.commit()
            flash('Cahier modifié avec succès !', 'success')
            return redirect(url_for('cahier.list_cahiers'))
        except Exception as e:
            db.session.rollback()  # Annuler la transaction en cas d'erreur
            logging.error(f"Erreur lors de la modification du cahier: {e}")  # Journaliser l'erreur
            flash('Erreur lors de la modification du cahier. Veuillez réessayer.', 'danger')

    template = f'cahier/{cahier.type}.html'
    return render_template(template, cahier=cahier, mode='edit')


# ============================================================
# SUPPRIMER UN CAHIER
# ============================================================
@cahier_bp.route('/delete/<int:cahier_id>', methods=['POST'])
@login_required
def delete(cahier_id):
    cahier = CahierCharge.query.get_or_404(cahier_id)

    if cahier.user_id != current_user.id:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('cahier.list_cahiers'))

    try:
        db.session.delete(cahier)
        db.session.commit()
        flash('Cahier supprimé avec succès.', 'success')
    except Exception as e:
        db.session.rollback()  # Annuler la transaction en cas d'erreur
        logging.error(f"Erreur lors de la suppression du cahier: {e}")  # Journaliser l'erreur
        flash('Erreur lors de la suppression du cahier. Veuillez réessayer.', 'danger')

    return redirect(url_for('cahier.list_cahiers'))


# ============================================================
# TÉLÉCHARGER UN CAHIER (PDF)
# ============================================================
@cahier_bp.route('/download/<int:cahier_id>')
@login_required
def download(cahier_id):
    cahier = CahierCharge.query.get_or_404(cahier_id)

    if cahier.user_id != current_user.id:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('cahier.list_cahiers'))

    # TODO: Générer le PDF avec ReportLab
    flash('Génération PDF en cours de développement.', 'info')
    return redirect(url_for('cahier.list_cahiers'))
