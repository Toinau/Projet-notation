from . import db
from datetime import datetime
import re
from sqlalchemy.orm import relationship
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prenom = db.Column(db.String(100), nullable=False)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='coureur')
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    team = relationship('Team', back_populates='users')

    def __repr__(self):
        return f'<User {self.prenom} {self.nom} - {self.role}>'

    def is_admin(self):
        return self.role == 'admin'

    def is_coureur(self):
        return self.role == 'coureur'

    @staticmethod
    def validate_email(email):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_password(password):
        if len(password) < 8:
            return False, "Le mot de passe doit contenir au moins 8 caractères"
        if not re.search(r'[A-Z]', password):
            return False, "Le mot de passe doit contenir au moins une majuscule"
        if not re.search(r'[a-z]', password):
            return False, "Le mot de passe doit contenir au moins une minuscule"
        if not re.search(r'\d', password):
            return False, "Le mot de passe doit contenir au moins un chiffre"
        return True, "Mot de passe valide"

    @staticmethod
    def validate_nom(nom):
        if len(nom) < 2:
            return False, "Le nom doit contenir au moins 2 caractères"
        if not re.match(r'^[a-zA-ZÀ-ÿ\-\s]+$', nom):
            return False, "Le nom ne peut contenir que des lettres, espaces et tirets"
        return True, "Nom valide"

    @staticmethod
    def validate_prenom(prenom):
        if len(prenom) < 2:
            return False, "Le prénom doit contenir au moins 2 caractères"
        if not re.match(r'^[a-zA-ZÀ-ÿ\-\s]+$', prenom):
            return False, "Le prénom ne peut contenir que des lettres, espaces et tirets"
        return True, "Prénom valide"

    def get_id(self):
        return str(self.id)

class Questionnaire(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(200), nullable=False)
    course_date = db.Column(db.Date, nullable=False)
    direct_velo_points = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relation avec les participants
    participants = db.relationship('QuestionnaireParticipant', backref='questionnaire', lazy=True, cascade='all, delete-orphan')
    # Relation avec les réponses (ajout du cascade)
    responses = db.relationship('QuestionnaireResponse', backref='questionnaire', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Questionnaire {self.course_name} - {self.course_date}>'

class QuestionnaireParticipant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    questionnaire_id = db.Column(db.Integer, db.ForeignKey('questionnaire.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    has_responded = db.Column(db.Boolean, default=False, nullable=False)
    response_date = db.Column(db.DateTime, nullable=True)
    comment = db.Column(db.Text, nullable=True)  # Commentaire facultatif pour la soumission
    
    # Relation avec l'utilisateur
    user = db.relationship('User', backref='questionnaire_participations')
    
    def __repr__(self):
        return f'<QuestionnaireParticipant {self.questionnaire_id} - {self.user_id}>'

class QuestionnaireResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    questionnaire_id = db.Column(db.Integer, db.ForeignKey('questionnaire.id', ondelete='CASCADE'), nullable=False)
    evaluator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Coureur qui évalue
    evaluated_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Coureur évalué
    rating = db.Column(db.Integer, nullable=False)  # Note de 1 à 10
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    evaluator = db.relationship('User', foreign_keys=[evaluator_id], backref='evaluations_given')
    evaluated = db.relationship('User', foreign_keys=[evaluated_id], backref='evaluations_received')
    
    def __repr__(self):
        return f'<QuestionnaireResponse {self.evaluator_id} -> {self.evaluated_id}: {self.rating}/10>'

class Team(db.Model):
    __tablename__ = 'team'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(64), nullable=False, unique=True)
    description = db.Column(db.String(256))
    couleur = db.Column(db.String(16))
    actif = db.Column(db.Boolean, default=True)
    users = relationship('User', back_populates='team')

    def __repr__(self):
        return f'<Team {self.nom}>' 