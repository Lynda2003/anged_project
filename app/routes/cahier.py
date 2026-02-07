from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.cahier import CahierCharge
from datetime import datetime

cahier_bp = Blueprint('cahier', __name__, url_prefix='/cahiers')


@cahier_bp.route('/list')
@login_required
def list_cahiers():
    """Liste tous les cahiers avec filtres."""
    type_cahier = request.args.get('type', 'all')
    statut = request.args.get('statut', 'all')
    page = request.args.get('page', 1, type=int)

    # Construction de la requête
    query = CahierCharge.query.filter_by(user_id=current_user.id)

    if type_cahier != 'all':
        query = query.filter_by(type=type_cahier)
    if statut != 'all':
        query = query.filter_by(statut=statut)

    query = query.order_by(CahierCharge.created_at.desc())
    cahiers = query.paginate(page=page, per_page=9, error_out=False)

    # Gestion des requêtes HTMX
    if request.headers.get('HX-Request'):
        return render_template('cahier/_cahier_cards.html', cahiers=cahiers.items)

    return render_template('cahier/list.html',
                           cahiers=cahiers.items,
                           has_next=cahiers.has_next,
                           next_page=cahiers.next_num if cahiers.has_next else None,
                           type_filter=type_cahier,
                           statut_filter=statut)


@cahier_bp.route('/create/recyclage', methods=['GET', 'POST'])
@login_required
def create_recyclage():
    """Créer un cahier RECYCLAGE (81 champs)."""
    if request.method == 'POST':
        form_data = gather_form_data(request)
        cahier = CahierCharge(
            user_id=current_user.id,
            type='recyclage',
            titre=form_data.get('raison_sociale', '') + ' - Recyclage',
            nom_entreprise=form_data.get('raison_sociale', ''),
            donnees_formulaire=form_data,
            statut='brouillon'
        )

        db.session.add(cahier)
        db.session.commit()

        flash('✅ Cahier de charge Recyclage créé avec succès !', 'success')
        return redirect(url_for('cahier.view', cahier_id=cahier.id))

    return render_template('cahier/recyclage_create.html', mode='create', cahier=None)


@cahier_bp.route('/create/stockage', methods=['GET', 'POST'])
@login_required
def create_stockage():
    """Créer un cahier STOCKAGE (86 champs)."""
    if request.method == 'POST':
        form_data = gather_form_data(request, stockage=True)
        cahier = CahierCharge(
            user_id=current_user.id,
            type='stockage',
            titre=form_data.get('raison_sociale', '') + ' - Stockage',
            nom_entreprise=form_data.get('raison_sociale', ''),
            donnees_formulaire=form_data,
            statut='brouillon'
        )

        db.session.add(cahier)
        db.session.commit()

        flash('✅ Cahier de charge Stockage créé avec succès !', 'success')
        return redirect(url_for('cahier.view', cahier_id=cahier.id))

    return render_template('cahier/stockage_create.html', mode='create', cahier=None)


@cahier_bp.route('/view/<int:cahier_id>')
@login_required
def view(cahier_id):
    """Afficher un cahier en lecture seule."""
    cahier = CahierCharge.query.get_or_404(cahier_id)

    if cahier.user_id != current_user.id:
        flash('❌ Accès non autorisé.', 'danger')
        return redirect(url_for('cahier.list_cahiers'))

    template = 'cahier/recyclage_view.html' if cahier.type == 'recyclage' else 'cahier/stockage_view.html'
    return render_template(template, cahier=cahier, mode='view')


@cahier_bp.route('/edit/<int:cahier_id>', methods=['GET', 'POST'])
@login_required
def edit(cahier_id):
    """Modifier un cahier (seulement si brouillon)."""
    cahier = CahierCharge.query.get_or_404(cahier_id)

    if cahier.user_id != current_user.id:
        flash('❌ Accès non autorisé.', 'danger')
        return redirect(url_for('cahier.list_cahiers'))

    if not cahier.is_editable():
        flash('⚠️ Seuls les cahiers en brouillon peuvent être modifiés.', 'warning')
        return redirect(url_for('cahier.view', cahier_id=cahier_id))

    if request.method == 'POST':
        form_data = gather_form_data(request, cahier.type == 'stockage')

        # Mise à jour du cahier
        cahier.donnees_formulaire = form_data
        cahier.titre = form_data.get('raison_sociale', '') + f' - {cahier.type.capitalize()}'
        cahier.nom_entreprise = form_data.get('raison_sociale', '')
        cahier.updated_at = datetime.utcnow()

        db.session.commit()
        flash('✅ Cahier modifié avec succès !', 'success')
        return redirect(url_for('cahier.view', cahier_id=cahier_id))

    template = 'cahier/recyclage_create.html' if cahier.type == 'recyclage' else 'cahier/stockage_create.html'
    return render_template(template, cahier=cahier, mode='edit')


@cahier_bp.route('/submit/<int:cahier_id>', methods=['POST'])
@login_required
def submit(cahier_id):
    """Soumettre un cahier (brouillon → soumis)."""
    cahier = CahierCharge.query.get_or_404(cahier_id)

    if cahier.user_id != current_user.id:
        flash('❌ Accès non autorisé.', 'danger')
        return redirect(url_for('cahier.list_cahiers'))

    if not cahier.can_submit():
        flash('⚠️ Veuillez remplir tous les champs obligatoires.', 'warning')
        return redirect(url_for('cahier.edit', cahier_id=cahier_id))

    cahier.statut = 'soumis'
    cahier.date_soumission = datetime.utcnow()
    db.session.commit()

    flash('✅ Cahier soumis avec succès pour validation ANGED !', 'success')
    return redirect(url_for('cahier.view', cahier_id=cahier_id))


@cahier_bp.route('/delete/<int:cahier_id>', methods=['POST'])
@login_required
def delete(cahier_id):
    """Supprimer un cahier (si brouillon)."""
    cahier = CahierCharge.query.get_or_404(cahier_id)

    if cahier.user_id != current_user.id or not cahier.is_deletable():
        flash('❌ Impossible de supprimer ce cahier.', 'danger')
        return redirect(url_for('cahier.list_cahiers'))

    db.session.delete(cahier)
    db.session.commit()

    flash('✅ Cahier supprimé avec succès.', 'success')
    return redirect(url_for('cahier.list_cahiers'))


@cahier_bp.route('/autosave/<int:cahier_id>', methods=['POST'])
@login_required
def autosave(cahier_id):
    """Sauvegarde automatique (AJAX)."""
    cahier = CahierCharge.query.get_or_404(cahier_id)

    if cahier.user_id != current_user.id or not cahier.is_editable():
        return jsonify({'success': False}), 403

    form_data = request.get_json()
    cahier.donnees_formulaire = form_data
    cahier.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'success': True,
        'timestamp': cahier.updated_at.strftime('%H:%M:%S'),
        'completion': cahier.get_completion_percentage()
    })


def gather_form_data(request, stockage=False):
    """Rassembler et normaliser les données du formulaire."""
    form_data = request.form.to_dict()

    # Gestion des champs multi-sélection
    if stockage:
        form_data['nature_activite_stockage'] = request.form.getlist('nature_activite_stockage')
        form_data['types_dechets_stockes'] = request.form.getlist('types_dechets_stockes')
        form_data['modes_stockage'] = request.form.getlist('modes_stockage')
        form_data['equipements_manutention'] = request.form.getlist('equipements_manutention')
    else:
        form_data['nature_activite'] = request.form.getlist('nature_activite')
        form_data['types_dechets'] = request.form.getlist('types_dechets')
        form_data['origine_dechets'] = request.form.getlist('origine_dechets')
        form_data['certifications'] = request.form.getlist('certifications')

    return form_data
