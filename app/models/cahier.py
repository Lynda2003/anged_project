
from app import db
from datetime import datetime


class CahierCharge(db.Model):
    """Modèle pour les Cahiers de Charge"""

    __tablename__ = 'cahiers_charge'

    # Colonnes principales
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    type = db.Column(db.String(20), nullable=False, index=True)  # 'recyclage' ou 'stockage'
    titre = db.Column(db.String(200), nullable=False)
    nom_entreprise = db.Column(db.String(200), index=True)
    donnees_formulaire = db.Column(db.JSON, nullable=True)  # Contient les 81 ou 86 champs
    # Statuts : 'brouillon', 'soumis', 'valide', 'refuse'
    statut = db.Column(db.String(30), default='brouillon', index=True)

    commentaire_admin = db.Column(db.Text, nullable=True)
    date_soumission = db.Column(db.DateTime, nullable=True)
    date_validation = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<CahierCharge {self.titre} ({self.type})>'

    # Méthodes d'accès aux données JSON
    def get_field(self, field_name, default=''):
        """Récupérer une valeur du JSON de manière sécurisée."""
        return self.donnees_formulaire.get(field_name, default) if self.donnees_formulaire else default

    def get_multi_field(self, field_name, default=None):
        """Récupérer un champ multi-sélection (liste)."""
        value = self.get_field(field_name, default or [])
        return value if isinstance(value, list) else default or []

    # Propriétés pour accès rapide
    @property
    def raison_sociale(self):
        return self.get_field('raison_sociale')

    @property
    def matricule_fiscal(self):
        return self.get_field('matricule_fiscal')

    @property
    def telephone(self):
        return self.get_field('telephone')

    @property
    def email(self):
        return self.get_field('email')

    @property
    def gouvernorat(self):
        return self.get_field('gouvernorat')

    # Méthodes de vérification
    def is_editable(self):
        """Un cahier n'est éditable que s'il est en brouillon."""
        return self.statut == 'brouillon'

    def is_deletable(self):
        """Un cahier n'est supprimable que s'il est en brouillon."""
        return self.statut == 'brouillon'

    def can_submit(self):
        """Vérifier si le cahier peut être soumis."""
        if self.statut != 'brouillon':
            return False

        # Vérifier les champs obligatoires minimaux
        required_fields = ['raison_sociale', 'matricule_fiscal', 'telephone', 'email']
        return all(self.get_field(field) for field in required_fields)

    def get_completion_percentage(self):
        """Calculer le pourcentage de complétion."""
        if not self.donnees_formulaire:
            return 0

        total_fields = 81 if self.type == 'recyclage' else 86
        filled_fields = sum(1 for v in self.donnees_formulaire.values() if v not in (None, '', [])
                            )
        return int((filled_fields / total_fields) * 100)

    def get_badge_color(self):
        """Retourner les couleurs pour le badge de statut."""
        colors = {
            'brouillon': ('gray-100', 'gray-800', 'pencil-alt'),
            'soumis': ('yellow-100', 'yellow-800', 'clock'),
            'valide': ('green-100', 'green-800', 'check-circle'),
            'refuse': ('red-100', 'red-800', 'times-circle')
        }
        return colors.get(self.statut, ('gray-100', 'gray-800', 'question'))
