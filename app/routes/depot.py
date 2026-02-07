from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models.document import Document
from app.models.depot import Depot
import os

# Création du blueprint — nom EXACTEMENT "depot_bp"
depot_bp = Blueprint('depot', __name__, url_prefix='/depot')

# Extensions autorisées pour l'upload
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE_MB = 5


def allowed_file(filename):
    """Vérifie si l'extension du fichier est autorisée."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ============================================================
# PAGE DOCUMENTS
# ============================================================


@depot_bp.route('/documents')
@login_required
def documents():
    """Page de gestion des documents du dépôt."""

    # Récupérer le dépôt de l'utilisateur
    depot = Depot.query.filter_by(user_id=current_user.id).first()

    # Récupérer les documents existants
    docs = {}
    if depot:
        for doc_type in ['RNE', 'CNSS', 'Patente']:
            docs[doc_type] = Document.query.filter_by(
                depot_id=depot.id,
                type_doc=doc_type
            ).order_by(Document.uploaded_at.desc()).first()

    return render_template('depot/documents.html', depot=depot, docs=docs)

# ============================================================
# UPLOAD DE FICHIER
# ============================================================


@depot_bp.route('/upload/<type_doc>', methods=['POST'])
@login_required
def upload(type_doc):
    """Upload d'un document (RNE, CNSS, Patente)"""

    # Vérifier le type de document
    if type_doc not in ['RNE', 'CNSS', 'Patente']:
        return jsonify({'error': 'Type de document invalide'}), 400

    # Vérifier qu'un fichier a été envoyé
    if 'file' not in request.files or request.files['file'].filename == '':
        return jsonify({'error': 'Aucun fichier sélectionné'}), 400

    file = request.files['file']

    # Vérifier l'extension
    if not allowed_file(file.filename):
        return jsonify({'error': 'Extension non autorisée. Utilisez : PDF, JPG, PNG'}), 400

    # Vérifier la taille
    file.seek(0, os.SEEK_END)  # Aller à la fin du fichier
    file_size = file.tell()
    file.seek(0)  # Retour au début

    if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
        return jsonify({'error': f'Fichier trop grand. Maximum : {MAX_FILE_SIZE_MB}MB'}), 400

    # Récupérer ou créer le dépôt
    depot = Depot.query.filter_by(user_id=current_user.id).first()
    if not depot:
        depot = Depot(
            user_id=current_user.id,
            nom_depot=f'Dépôt {current_user.prenom} {current_user.nom}',
            adresse='À compléter'
        )
        db.session.add(depot)
        db.session.commit()

    # Sécuriser le nom du fichier
    filename = secure_filename(file.filename)
    filename = f"{current_user.id}_{type_doc}_{filename}"

    # Créer le dossier de destination
    upload_folder = os.path.join(
        current_app.config.get('UPLOAD_FOLDER', 'app/static/uploads'),
        'documents',
        type_doc
    )

    os.makedirs(upload_folder, exist_ok=True)  # Crée le dossier s'il n'existe pas

    # Chemin complet
    filepath = os.path.join(upload_folder, filename)

    try:
        # Sauvegarder le fichier
        file.save(filepath)

        # Enregistrer en base de données
        document = Document(
            depot_id=depot.id,
            type_doc=type_doc,
            fichier_nom=filename,
            fichier_path=filepath,
            statut_verif='en_attente'
        )
        db.session.add(document)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Document {type_doc} uploadé avec succès !',
            'filename': filename
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erreur lors de l\'upload : {str(e)}'}), 500

# ============================================================
# LISTE DES DOCUMENTS
# ============================================================


@depot_bp.route('/list')
@login_required
def list_documents():
    """Liste les documents du dépôt de l'utilisateur."""
    depot = Depot.query.filter_by(user_id=current_user.id).first()

    docs = {}
    if depot:
        for doc_type in ['RNE', 'CNSS', 'Patente']:
            doc = Document.query.filter_by(
                depot_id=depot.id,
                type_doc=doc_type
            ).order_by(Document.uploaded_at.desc()).first()

            docs[doc_type] = {
                'id': doc.id,
                'fichier_nom': doc.fichier_nom,
                'statut': doc.statut_verif,
                'date': doc.uploaded_at.strftime('%d/%m/%Y') if doc and doc.uploaded_at else None
            } if doc else None
    else:
        # Si aucun dépôt n'est trouvé, retourner None pour chaque type de document
        docs = {doc_type: None for doc_type in ['RNE', 'CNSS', 'Patente']}

    return jsonify(docs)
