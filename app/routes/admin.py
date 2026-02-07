"""
Routes pour l'interface administrateur
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.depot import Depot
from app.models.document import Document
from app.models.cahier import CahierCharge
from app.models.suivi import Suivi, HistoriqueSuivi
from app.utils.decorators import admin_required
from datetime import datetime, timedelta
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ============================================================================
# DASHBOARD ADMIN
# ============================================================================


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Dashboard administrateur avec statistiques"""

    # Récupération des statistiques générales
    stats = {
        'total_users': User.query.filter_by(role='user').count(),
        'total_depots': Depot.query.count(),
        'total_cahiers': CahierCharge.query.count(),
        'documents_en_attente': Document.query.filter_by(statut_verif='en_attente').count(),
        'documents_valides': Document.query.filter_by(statut_verif='valide').count(),
        'documents_refuses': Document.query.filter_by(statut_verif='refuse').count(),
    }

    # Récupération des statuts des dépôts
    statuts_depots = db.session.query(Suivi.statut, func.count(Suivi.id)).group_by(Suivi.statut).all()
    stats['statuts'] = {'vert': 0, 'orange': 0, 'rouge': 0}

    for statut, count in statuts_depots:
        stats['statuts'][statut] = count

    # Activité récente (dernières vérifications)
    activites_recentes = HistoriqueSuivi.query.order_by(HistoriqueSuivi.date_modification.desc()).limit(10).all()

    # Documents en attente urgents (>7 jours)
    date_limite = datetime.utcnow() - timedelta(days=7)
    documents_urgents = Document.query.filter(
        Document.statut_verif == 'en_attente', Document.uploaded_at < date_limite).count()
    stats['documents_urgents'] = documents_urgents

    return render_template('admin/dashboard.html', stats=stats, activites=activites_recentes)

# ============================================================================
# VÉRIFICATION DES DOCUMENTS
# ============================================================================


@admin_bp.route('/verify')
@login_required
@admin_required
def verify_documents():
    """Liste des documents à vérifier"""

    # Récupération des filtres
    type_doc = request.args.get('type', 'all')
    statut = request.args.get('statut', 'en_attente')
    page = request.args.get('page', 1, type=int)

    # Construire la requête
    query = Document.query

    # Filtres par type et statut
    if type_doc != 'all':
        query = query.filter_by(type_doc=type_doc)

    if statut != 'all':
        query = query.filter_by(statut_verif=statut)

    # Joindre avec dépôt et utilisateur pour afficher les infos
    query = query.join(Depot).join(User).order_by(Document.uploaded_at.asc())  # Ordonner par date d'upload

    # Pagination
    documents = query.paginate(page=page, per_page=20, error_out=False)

    return render_template(
        'admin/verify_documents.html',
        documents=documents,
        type_filter=type_doc,
        statut_filter=statut
    )


@admin_bp.route('/verify-document/<int:doc_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def verify_single_document(doc_id):
    """Vérifier un document spécifique"""

    document = Document.query.get_or_404(doc_id)

    if request.method == 'POST':
        # Récupérer les données du formulaire
        action = request.form.get('action')  # 'valider' ou 'refuser'
        commentaire = request.form.get('commentaire', '')

        # Mettre à jour le statut du document
        if action == 'valider':
            document.statut_verif = 'valide'
            flash(f'Document {document.type_doc} validé avec succès.', 'success')
        elif action == 'refuser':
            document.statut_verif = 'refuse'
            flash(f'Document {document.type_doc} refusé.', 'warning')

        # Mettre à jour les données d'audit
        document.date_verification = datetime.utcnow()
        document.admin_id = current_user.id
        document.commentaire_admin = commentaire

        db.session.commit()
        update_depot_status(document.depot_id)  # Mettre à jour le statut du dépôt

        return redirect(url_for('admin.verify_documents'))

    return render_template('admin/verify_single.html', document=document)


@admin_bp.route('/verify-document-ajax/<int:doc_id>', methods=['POST'])
@login_required
@admin_required
def verify_document_ajax(doc_id):
    """Vérification rapide via AJAX/HTMX"""

    document = Document.query.get_or_404(doc_id)
    data = request.get_json()
    action = data.get('action')
    commentaire = data.get('commentaire', '')

    # Mettre à jour le document
    if action == 'valider':
        document.statut_verif = 'valide'
        message = 'Document validé'
    elif action == 'refuser':
        document.statut_verif = 'refuse'
        message = 'Document refusé'
    else:
        return jsonify({'error': 'Action invalide'}), 400

    document.date_verification = datetime.utcnow()
    document.admin_id = current_user.id
    document.commentaire_admin = commentaire

    db.session.commit()
    new_status = update_depot_status(document.depot_id)  # Mettre à jour le statut du dépôt

    return jsonify({
        'success': True,
        'message': message,
        'document_id': doc_id,
        'nouveau_statut': document.statut_verif,
        'statut_depot': new_status
    })

# ============================================================================
# GESTION DES STATUTS
# ============================================================================


def update_depot_status(depot_id):
    """
    Met à jour automatiquement le statut d'un dépôt
    selon l'état de ses documents.

    Règles:
    - ROUGE: Au moins un document refusé
    - ORANGE: Documents manquants ou en attente
    - VERT: Tous les documents validés (RNE + CNSS + Patente)
    """
    depot = Depot.query.get(depot_id)

    # Récupérer tous les documents du dépôt
    documents = Document.query.filter_by(depot_id=depot_id).all()

    # Organiser les documents par type
    docs_by_type = {'RNE': None, 'CNSS': None, 'Patente': None}

    for doc in documents:
        if docs_by_type[doc.type_doc] is None or doc.uploaded_at > docs_by_type[doc.type_doc].uploaded_at:
            docs_by_type[doc.type_doc] = doc

    # Déterminer le statut
    statut = 'vert'  # Par défaut
    commentaire = ''

    # Vérifier si un document est refusé
    for type_doc, doc in docs_by_type.items():
        if doc and doc.statut_verif == 'refuse':
            statut = 'rouge'
            commentaire = f'Document {type_doc} refusé.'
            break

    # Si pas de refus, vérifier la validité des documents
    if statut != 'rouge':
        for type_doc, doc in docs_by_type.items():
            if doc is None:
                statut = 'orange'
                commentaire = f'Document {type_doc} manquant.'
                break
            elif doc.statut_verif == 'en_attente':
                statut = 'orange'
                commentaire = f'Document {type_doc} en attente de vérification.'
                break
            elif doc.statut_verif != 'valide':
                statut = 'orange'
                commentaire = f'Document {type_doc} non validé.'
                break

        if statut == 'vert':
            commentaire = 'Tous les documents sont validés.'

    # Créer ou mettre à jour le suivi
    suivi = Suivi.query.filter_by(depot_id=depot_id).first()

    if suivi is None:
        suivi = Suivi(depot_id=depot_id, admin_id=current_user.id, statut=statut, commentaire=commentaire)
        db.session.add(suivi)
    else:
        if suivi.statut != statut:
            historique = HistoriqueSuivi(
                suivi_id=suivi.id,
                ancien_statut=suivi.statut,
                nouveau_statut=statut,
                admin_id=current_user.id,
                commentaire=f'Changement: {suivi.statut} → {statut}'
            )
            db.session.add(historique)

        suivi.statut = statut
        suivi.commentaire = commentaire
        suivi.admin_id = current_user.id
        suivi.date_verification = datetime.utcnow()

    db.session.commit()
    return statut


@admin_bp.route('/depot/<int:depot_id>/status', methods=['POST'])
@login_required
@admin_required
def update_status_manual(depot_id):
    """Mettre à jour manuellement le statut d'un dépôt"""

    statut = request.form.get('statut')
    commentaire = request.form.get('commentaire', '')

    if statut not in ['vert', 'orange', 'rouge']:
        flash('Statut invalide', 'danger')
        return redirect(url_for('admin.verify_documents'))

    suivi = Suivi.query.filter_by(depot_id=depot_id).first()

    if suivi:
        if suivi.statut != statut:
            historique = HistoriqueSuivi(
                suivi_id=suivi.id,
                ancien_statut=suivi.statut,
                nouveau_statut=statut,
                admin_id=current_user.id,
                commentaire=commentaire
            )
            db.session.add(historique)

        suivi.statut = statut
        suivi.commentaire = commentaire
        suivi.admin_id = current_user.id
        suivi.date_verification = datetime.utcnow()
    else:
        suivi = Suivi(depot_id=depot_id, admin_id=current_user.id, statut=statut, commentaire=commentaire)
        db.session.add(suivi)

    db.session.commit()

    flash(f'Statut mis à jour : {statut.upper()}', 'success')
    return redirect(url_for('admin.verify_documents'))

# ============================================================================
# GESTION DES UTILISATEURS
# ============================================================================


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """Liste et gestion des utilisateurs"""

    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')

    query = User.query.filter_by(role='user')  # Exclure les admins

    # Recherche
    if search:
        query = query.filter(
            db.or_(
                User.email.ilike(f'%{search}%'),
                User.nom.ilike(f'%{search}%'),
                User.prenom.ilike(f'%{search}%')
            )
        )

    # Pagination
    users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=20, error_out=False)

    return render_template('admin/users.html', users=users, search=search)


@admin_bp.route('/users/<int:user_id>/toggle-active', methods=['POST'])
@login_required
@admin_required
def toggle_user_active(user_id):
    """Activer/Désactiver un utilisateur"""

    user = User.query.get_or_404(user_id)

    # Ne pas désactiver un admin
    if user.role == 'admin':
        flash('Impossible de modifier un administrateur.', 'danger')
        return redirect(url_for('admin.users'))

    user.actif = not user.actif
    db.session.commit()

    status = 'activé' if user.actif else 'désactivé'
    flash(f'Utilisateur {user.email} {status}.', 'success')

    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Supprimer un utilisateur"""

    user = User.query.get_or_404(user_id)

    # Ne pas supprimer un admin
    if user.role == 'admin':
        flash('Impossible de supprimer un administrateur.', 'danger')
        return redirect(url_for('admin.users'))

    # Supprimer l'utilisateur
    db.session.delete(user)
    db.session.commit()

    flash(f'Utilisateur {user.email} supprimé.', 'success')
    return redirect(url_for('admin.users'))

# ============================================================================
# STATISTIQUES ET RAPPORTS
# ============================================================================


@admin_bp.route('/statistics')
@login_required
@admin_required
def statistics():
    """Statistiques détaillées et rapports"""

    # Période
    period = request.args.get('period', '30')  # jours
    date_debut = datetime.utcnow() - timedelta(days=int(period))

    # Nouveaux utilisateurs
    new_users = User.query.filter(
        User.created_at >= date_debut,
        User.role == 'user'
    ).count()

    # Nouveaux cahiers
    new_cahiers = CahierCharge.query.filter(
        CahierCharge.created_at >= date_debut
    ).count()

    # Documents vérifiés
    docs_verifies = Document.query.filter(
        Document.date_verification >= date_debut
    ).count()

    # Évolution des statuts (graphique)
    statuts_evolution = db.session.query(
        func.date(HistoriqueSuivi.date_modification).label('date'),
        HistoriqueSuivi.nouveau_statut,
        func.count(HistoriqueSuivi.id)
    ).filter(
        HistoriqueSuivi.date_modification >= date_debut
    ).group_by(
        func.date(HistoriqueSuivi.date_modification),
        HistoriqueSuivi.nouveau_statut
    ).all()

    # Transformer les données pour le graphique
    graph_data = {}
    for date, statut, count in statuts_evolution:
        date_str = date.strftime('%Y-%m-%d')
        if date_str not in graph_data:
            graph_data[date_str] = {'vert': 0, 'orange': 0, 'rouge': 0}
        graph_data[date_str][statut] = count

    stats = {
        'new_users': new_users,
        'new_cahiers': new_cahiers,
        'docs_verifies': docs_verifies,
        'period': period,
        'graph_data': graph_data
    }

    return render_template('admin/statistics.html', stats=stats)


@admin_bp.route('/export/rapport-mensuel')
@login_required
@admin_required
def export_rapport_mensuel():
    """Générer un rapport mensuel en PDF"""

    # TODO: Implémenter génération PDF avec ReportLab
    flash('Fonctionnalité en cours de développement.', 'info')
    return redirect(url_for('admin.statistics'))
