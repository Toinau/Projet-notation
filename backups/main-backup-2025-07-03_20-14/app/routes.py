from flask import Blueprint, render_template, redirect, url_for, request, flash, session, abort, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User, Questionnaire, QuestionnaireParticipant, QuestionnaireResponse
from app.decorators import login_required, admin_required, coureur_required
from app import db, mail, serializer
from flask_mail import Message
from itsdangerous import SignatureExpired, BadSignature
from datetime import datetime
from sqlalchemy import func, case

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']
        role = request.form.get('role', 'coureur')
        errors = []
        is_valid_username, username_msg = User.validate_username(username)
        if not is_valid_username:
            errors.append(username_msg)
        if not User.validate_email(email):
            errors.append("Format d'email invalide")
        is_valid_password, password_msg = User.validate_password(password)
        if not is_valid_password:
            errors.append(password_msg)
        if role not in ['coureur', 'admin']:
            role = 'coureur'
        if User.query.filter_by(username=username).first():
            errors.append('Nom d\'utilisateur déjà utilisé')
        if User.query.filter_by(email=email).first():
            errors.append('Email déjà utilisé')
        if errors:
            for error in errors:
                flash(error, 'danger')
            return redirect(url_for('main.register'))
        try:
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(username=username, email=email, password=hashed_password, role=role)
            db.session.add(new_user)
            db.session.commit()
            flash(f'Votre compte {role} a été créé avec succès!', 'success')
            return redirect(url_for('main.login'))
        except Exception as e:
            db.session.rollback()
            flash('Erreur lors de la création du compte. Veuillez réessayer.', 'danger')
            current_app.logger.error(f"Erreur création utilisateur: {e}")
            return redirect(url_for('main.register'))
    return render_template('register.html')

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        remember = True if request.form.get('remember') else False
        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password, password):
            flash('Veuillez vérifier vos identifiants et réessayer.', 'danger')
            return redirect(url_for('main.login'))
        if not user.is_active:
            flash('Votre compte a été désactivé. Contactez l\'administrateur.', 'danger')
            return redirect(url_for('main.login'))
        try:
            session.permanent = remember
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            current_app.logger.info(f"Connexion réussie: {user.username} ({user.role})")
            flash(f'Bienvenue, {user.username} ({user.role})!', 'success')
            if user.role == 'admin':
                return redirect(url_for('main.admin_dashboard'))
            else:
                return redirect(url_for('main.coureur_dashboard'))
        except Exception as e:
            current_app.logger.error(f"Erreur lors de la connexion: {e}")
            flash('Erreur lors de la connexion. Veuillez réessayer.', 'danger')
            return redirect(url_for('main.login'))
    return render_template('login.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    user = User.query.get(session['user_id'])
    if user is None:
        flash('Utilisateur non trouvé.', 'danger')
        return redirect(url_for('main.login'))
    if user.role == 'admin':
        return redirect(url_for('main.admin_dashboard'))
    else:
        return redirect(url_for('main.coureur_dashboard'))

@main_bp.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    try:
        current_user = User.query.get(session['user_id'])
        total_users = User.query.count()
        total_coureurs = User.query.filter_by(role='coureur').count()
        total_admins = User.query.filter_by(role='admin').count()
        active_users = User.query.filter_by(is_active=True).count()
        inactive_users = User.query.filter_by(is_active=False).count()
        all_users = User.query.order_by(User.created_at.desc()).all()
        stats = {
            'total_users': total_users,
            'total_coureurs': total_coureurs,
            'total_admins': total_admins,
            'active_users': active_users,
            'inactive_users': inactive_users
        }
        return render_template('admin/dashboard.html', username=session['username'], current_user=current_user, all_users=all_users, stats=stats)
    except Exception as e:
        current_app.logger.error(f"Erreur dashboard admin: {e}")
        flash('Erreur lors du chargement du dashboard.', 'danger')
        return redirect(url_for('main.dashboard'))

@main_bp.route('/admin/users')
@admin_required
def admin_users():
    try:
        users = User.query.order_by(User.created_at.desc()).all()
        current_user_id = session['user_id']
        return render_template('admin/users.html', users=users, current_user_id=current_user_id)
    except Exception as e:
        current_app.logger.error(f"Erreur liste utilisateurs: {e}")
        flash('Erreur lors du chargement des utilisateurs.', 'danger')
        return redirect(url_for('main.admin_dashboard'))

@main_bp.route('/admin/users/<int:user_id>/toggle', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    try:
        user = User.query.get_or_404(user_id)
        if user.id == session['user_id']:
            flash('Vous ne pouvez pas désactiver votre propre compte.', 'warning')
            return redirect(url_for('main.admin_users'))
        user.is_active = not user.is_active
        db.session.commit()
        status = 'activé' if user.is_active else 'désactivé'
        flash(f'Le compte de {user.username} a été {status}.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur toggle user status: {e}")
        flash('Erreur lors de la modification du statut.', 'danger')
    return redirect(url_for('main.admin_users'))

@main_bp.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        if user.id == session['user_id']:
            flash('Vous ne pouvez pas supprimer votre propre compte.', 'warning')
            return redirect(url_for('main.admin_users'))
        username = user.username
        db.session.delete(user)
        db.session.commit()
        flash(f'Le compte de {username} a été supprimé.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur suppression utilisateur: {e}")
        flash('Erreur lors de la suppression.', 'danger')
    return redirect(url_for('main.admin_users'))

@main_bp.route('/admin/users/<int:user_id>/promote', methods=['POST'])
@admin_required
def promote_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        if user.role == 'coureur':
            user.role = 'admin'
            db.session.commit()
            flash(f'{user.username} a été promu administrateur.', 'success')
        else:
            flash(f'{user.username} est déjà administrateur.', 'info')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur promotion utilisateur: {e}")
        flash('Erreur lors de la promotion.', 'danger')
    return redirect(url_for('main.admin_users'))

@main_bp.route('/admin/users/<int:user_id>/demote', methods=['POST'])
@admin_required
def demote_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        if user.id == session['user_id']:
            flash('Vous ne pouvez pas modifier votre propre rôle.', 'warning')
            return redirect(url_for('main.admin_users'))
        if user.role == 'admin':
            user.role = 'coureur'
            db.session.commit()
            flash(f'{user.username} a été rétrogradé en coureur.', 'success')
        else:
            flash(f'{user.username} est déjà coureur.', 'info')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur rétrogradation utilisateur: {e}")
        flash('Erreur lors de la rétrogradation.', 'danger')
    return redirect(url_for('main.admin_users'))

@main_bp.route('/admin/create-questionnaire', methods=['GET', 'POST'])
@admin_required
def create_questionnaire():
    if request.method == 'POST':
        try:
            # Récupération des données du formulaire
            course_name = request.form.get('course_name', '').strip()
            course_date = request.form.get('course_date', '')
            direct_velo_points = request.form.get('direct_velo_points', '').strip()
            present_coureurs = request.form.getlist('present_coureurs')  # Liste des IDs des coureurs présents
            
            # Validation des données
            errors = []
            if not course_name:
                errors.append("Le nom de la course est requis")
            if not course_date:
                errors.append("La date de la course est requise")
            if not direct_velo_points:
                errors.append("Le nombre de points Direct Vélo est requis")
            elif not direct_velo_points.isdigit() or int(direct_velo_points) < 0:
                errors.append("Le nombre de points Direct Vélo doit être un nombre positif")
            if not present_coureurs:
                errors.append("Au moins un coureur doit être sélectionné")
            
            if errors:
                for error in errors:
                    flash(error, 'danger')
                return render_template('admin/create_questionnaire.html', coureurs=get_coureurs_list())
            
            # Création du questionnaire
            questionnaire = Questionnaire(
                course_name=course_name,
                course_date=datetime.strptime(course_date, '%Y-%m-%d').date(),
                direct_velo_points=int(direct_velo_points),
                created_by=session['user_id']
            )
            db.session.add(questionnaire)
            db.session.flush()  # Pour obtenir l'ID du questionnaire
            
            # Ajout des participants
            for coureur_id in present_coureurs:
                participant = QuestionnaireParticipant(
                    questionnaire_id=questionnaire.id,
                    user_id=int(coureur_id)
                )
                db.session.add(participant)
            
            db.session.commit()
            
            nb_coureurs = len(present_coureurs)
            flash(f'Questionnaire créé avec succès pour la course "{course_name}" avec {nb_coureurs} coureurs et {direct_velo_points} points Direct Vélo!', 'success')
            return redirect(url_for('main.admin_dashboard'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur création questionnaire: {e}")
            flash('Erreur lors de la création du questionnaire.', 'danger')
            return render_template('admin/create_questionnaire.html', coureurs=get_coureurs_list())
    
    return render_template('admin/create_questionnaire.html', coureurs=get_coureurs_list())

def get_coureurs_list():
    """Récupère la liste des coureurs actifs pour l'affichage"""
    try:
        return User.query.filter_by(role='coureur', is_active=True).order_by(User.username).all()
    except Exception as e:
        current_app.logger.error(f"Erreur récupération coureurs: {e}")
        return []

@main_bp.route('/coureur/dashboard')
@coureur_required
def coureur_dashboard():
    try:
        current_user = User.query.get(session['user_id'])
        
        # Calculer le nombre de questionnaires à remplir (en attente)
        user_id = session['user_id']
        nb_questionnaires = QuestionnaireParticipant.query.filter_by(user_id=user_id, has_responded=False).count()
        
        # Calculer le classement du coureur
        classement_mois, classement_annee = calculate_coureur_ranking(user_id)
        
        return render_template('coureur/dashboard.html', 
                             username=session['username'], 
                             current_user=current_user,
                             nb_questionnaires=nb_questionnaires,
                             classement_mois=classement_mois,
                             classement_annee=classement_annee)
    except Exception as e:
        current_app.logger.error(f"Erreur dashboard coureur: {e}")
        flash('Erreur lors du chargement du dashboard.', 'danger')
        return redirect(url_for('main.dashboard'))

def calculate_coureur_ranking(user_id):
    """
    Calcule le classement d'un coureur basé sur les points gagnés
    Points = Points Direct Vélo × Note moyenne reçue par course
    """
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import func
        
        # Obtenir la date actuelle
        now = datetime.utcnow()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_of_year = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Récupérer tous les coureurs
        all_coureurs = User.query.filter_by(role='coureur', is_active=True).all()
        
        # Calculer les points pour tous les coureurs
        coureurs_rankings = []
        
        for coureur in all_coureurs:
            # Récupérer toutes les participations du coureur
            participations = db.session.query(
                QuestionnaireParticipant, Questionnaire
            ).join(
                Questionnaire, QuestionnaireParticipant.questionnaire_id == Questionnaire.id
            ).filter(
                QuestionnaireParticipant.user_id == coureur.id
            ).all()
            
            annual_points = 0
            monthly_points = 0
            
            for participation, questionnaire in participations:
                # Calculer la note moyenne reçue pour cette course
                avg_rating = db.session.query(func.avg(QuestionnaireResponse.rating)).filter(
                    QuestionnaireResponse.questionnaire_id == questionnaire.id,
                    QuestionnaireResponse.evaluated_id == coureur.id
                ).scalar() or 0
                
                # Calculer les points pour cette course
                course_points = questionnaire.direct_velo_points * float(avg_rating)
                
                # Ajouter aux points annuels
                annual_points += course_points
                
                # Ajouter aux points mensuels si la course est dans le mois en cours
                if questionnaire.course_date >= start_of_month.date():
                    monthly_points += course_points
            
            coureurs_rankings.append({
                'user_id': coureur.id,
                'username': coureur.username,
                'annual_points': round(annual_points, 1),
                'monthly_points': round(monthly_points, 1)
            })
        
        # Trier par points décroissants
        coureurs_rankings.sort(key=lambda x: x['annual_points'], reverse=True)
        
        # Trouver la position du coureur actuel
        user_position_annual = None
        for i, coureur in enumerate(coureurs_rankings):
            if coureur['user_id'] == user_id:
                user_position_annual = i + 1
                break
        
        # Trier par points mensuels décroissants
        coureurs_rankings.sort(key=lambda x: x['monthly_points'], reverse=True)
        
        # Trouver la position du coureur actuel
        user_position_monthly = None
        for i, coureur in enumerate(coureurs_rankings):
            if coureur['user_id'] == user_id:
                user_position_monthly = i + 1
                break
        
        # Formater les résultats
        if user_position_monthly is None or coureurs_rankings[0]['monthly_points'] == 0:
            classement_mois = "N/A"
        else:
            classement_mois = f"{user_position_monthly}ème"
            
        if user_position_annual is None or coureurs_rankings[0]['annual_points'] == 0:
            classement_annee = "N/A"
        else:
            classement_annee = f"{user_position_annual}ème"
        
        return classement_mois, classement_annee
        
    except Exception as e:
        current_app.logger.error(f"Erreur calcul classement: {e}")
        return "N/A", "N/A"

@main_bp.route('/debug-user')
def debug_user():
    if 'user_id' not in session:
        return "Non connecté"
    user = User.query.get(session['user_id'])
    if not user:
        return "Utilisateur non trouvé"
    debug_info = f"""
    <h2>Informations de debug</h2>
    <p><strong>Username:</strong> {user.username}</p>
    <p><strong>Email:</strong> {user.email}</p>
    <p><strong>Role (base):</strong> '{user.role}'</p>
    <p><strong>Role (session):</strong> '{session.get('role', 'Non défini')}'</p>
    <p><strong>is_admin():</strong> {user.is_admin()}</p>
    <p><strong>is_coureur():</strong> {user.is_coureur()}</p>
    <p><strong>is_active:</strong> {user.is_active}</p>
    <p><strong>User ID:</strong> {user.id}</p>
    <p><strong>Session User ID:</strong> {session.get('user_id', 'Non défini')}</p>
    <h3>Actions:</h3>
    <a href="/force-admin-role" style="background: red; color: white; padding: 10px; text-decoration: none;">Forcer le rôle admin</a><br><br>
    <a href="/dashboard" style="background: blue; color: white; padding: 10px; text-decoration: none;">Aller au dashboard</a><br><br>
    <a href="/logout" style="background: gray; color: white; padding: 10px; text-decoration: none;">Se déconnecter</a>
    """
    return debug_info

@main_bp.route('/force-admin-role')
@login_required
def force_admin_role():
    try:
        user = User.query.get(session['user_id'])
        if user is None:
            flash('Utilisateur non trouvé.', 'danger')
            return redirect(url_for('main.login'))
        user.role = 'admin'
        user.is_active = True
        db.session.commit()
        session['role'] = 'admin'
        flash(f'Rôle admin forcé pour {user.username}', 'success')
        return redirect(url_for('main.debug_user'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur force admin role: {e}")
        flash('Erreur lors de la modification du rôle.', 'danger')
        return redirect(url_for('main.debug_user'))

@main_bp.route('/logout')
def logout():
    try:
        session.pop('user_id', None)
        session.pop('username', None)
        session.pop('role', None)
        flash('Vous avez été déconnecté.', 'info')
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la déconnexion: {e}")
    return redirect(url_for('main.index'))

@main_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        try:
            user = User.query.get(session['user_id'])
            if user is None:
                flash('Utilisateur non trouvé.', 'danger')
                return redirect(url_for('main.login'))
            if not check_password_hash(user.password, current_password):
                flash('Mot de passe actuel incorrect.', 'danger')
                return redirect(url_for('main.change_password'))
            if new_password != confirm_password:
                flash('Les nouveaux mots de passe ne correspondent pas.', 'danger')
                return redirect(url_for('main.change_password'))
            is_valid, message = User.validate_password(new_password)
            if not is_valid:
                flash(message, 'danger')
                return redirect(url_for('main.change_password'))
            user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
            db.session.commit()
            flash('Mot de passe mis à jour avec succès.', 'success')
            return redirect(url_for('main.dashboard'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur changement mot de passe: {e}")
            flash('Erreur lors du changement de mot de passe.', 'danger')
            return redirect(url_for('main.change_password'))
    return render_template('change_password.html')

@main_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        try:
            user = User.query.filter_by(email=email).first()
            if user:
                token = serializer.dumps(user.email, salt='reset-password')
                link = url_for('main.reset_password', token=token, _external=True)
                msg = Message('Réinitialisation de votre mot de passe', recipients=[email])
                msg.body = f'Cliquez sur ce lien pour réinitialiser votre mot de passe : {link}'
                mail.send(msg)
            flash("Si l'adresse e-mail existe, un lien a été envoyé.", 'info')
        except Exception as e:
            current_app.logger.error(f"Erreur envoi email reset: {e}")
            flash('Erreur lors de l\'envoi de l\'email.', 'danger')
        return redirect(url_for('main.login'))
    return render_template('forgot_password.html')

@main_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='reset-password', max_age=3600)
    except Exception:
        flash('Le lien est invalide ou expiré.', 'danger')
        return redirect(url_for('main.login'))
    if request.method == 'POST':
        new_password = request.form['password']
        try:
            user = User.query.filter_by(email=email).first()
            if user is None:
                flash('Utilisateur non trouvé.', 'danger')
                return redirect(url_for('main.login'))
            is_valid, message = User.validate_password(new_password)
            if not is_valid:
                flash(message, 'danger')
                return render_template('reset_password.html')
            user.password = generate_password_hash(new_password)
            db.session.commit()
            flash('Mot de passe modifié avec succès.', 'success')
            return redirect(url_for('main.login'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur reset password: {e}")
            flash('Erreur lors de la réinitialisation du mot de passe.', 'danger')
    return render_template('reset_password.html')

@main_bp.route('/coureur/questionnaires')
@coureur_required
def coureur_questionnaires():
    try:
        # Récupérer les questionnaires où le coureur est participant
        user_id = session['user_id']
        participations = QuestionnaireParticipant.query.filter_by(user_id=user_id).all()
        
        questionnaires = []
        for participation in participations:
            questionnaire = participation.questionnaire
            questionnaires.append({
                'id': questionnaire.id,
                'course_name': questionnaire.course_name,
                'course_date': questionnaire.course_date,
                'direct_velo_points': questionnaire.direct_velo_points,
                'has_responded': participation.has_responded,
                'response_date': participation.response_date
            })
        
        # Trier par date de course (plus récent en premier)
        questionnaires.sort(key=lambda x: x['course_date'], reverse=True)
        
        return render_template('coureur/questionnaires.html', questionnaires=questionnaires)
        
    except Exception as e:
        current_app.logger.error(f"Erreur récupération questionnaires: {e}")
        flash('Erreur lors du chargement des questionnaires.', 'danger')
        return redirect(url_for('main.coureur_dashboard'))

@main_bp.route('/coureur/questionnaire/<int:questionnaire_id>/fill', methods=['GET', 'POST'])
@coureur_required
def fill_questionnaire(questionnaire_id):
    try:
        user_id = session['user_id']
        
        # Vérifier que le coureur est participant à ce questionnaire
        participation = QuestionnaireParticipant.query.filter_by(
            questionnaire_id=questionnaire_id, 
            user_id=user_id
        ).first()
        
        if not participation:
            flash('Vous n\'êtes pas autorisé à répondre à ce questionnaire.', 'danger')
            return redirect(url_for('main.coureur_questionnaires'))
        
        if participation.has_responded:
            flash('Vous avez déjà répondu à ce questionnaire.', 'info')
            return redirect(url_for('main.coureur_questionnaires'))
        
        questionnaire = Questionnaire.query.get_or_404(questionnaire_id)
        
        if request.method == 'POST':
            # Récupérer tous les participants du questionnaire
            participants = QuestionnaireParticipant.query.filter_by(questionnaire_id=questionnaire_id).all()
            
            # Validation des réponses
            errors = []
            responses = {}
            
            for participant in participants:
                rating_key = f'rating_{participant.user_id}'
                rating = request.form.get(rating_key, '').strip()
                
                if not rating:
                    errors.append(f"Veuillez noter {participant.user.username}")
                elif not rating.isdigit() or int(rating) < 1 or int(rating) > 10:
                    errors.append(f"La note pour {participant.user.username} doit être entre 1 et 10")
                else:
                    responses[participant.user_id] = int(rating)
            
            if errors:
                for error in errors:
                    flash(error, 'danger')
                return render_template('coureur/fill_questionnaire.html', 
                                     questionnaire=questionnaire, 
                                     participants=participants)
            
            # Sauvegarder les réponses
            try:
                for evaluated_id, rating in responses.items():
                    response = QuestionnaireResponse(
                        questionnaire_id=questionnaire_id,
                        evaluator_id=user_id,
                        evaluated_id=evaluated_id,
                        rating=rating
                    )
                    db.session.add(response)
                
                # Marquer le questionnaire comme répondu
                participation.has_responded = True
                participation.response_date = datetime.utcnow()
                
                db.session.commit()
                
                flash(f'Questionnaire pour "{questionnaire.course_name}" soumis avec succès!', 'success')
                return redirect(url_for('main.coureur_questionnaires'))
                
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Erreur sauvegarde réponses: {e}")
                flash('Erreur lors de la sauvegarde des réponses.', 'danger')
        
        # GET: Afficher le formulaire
        participants = QuestionnaireParticipant.query.filter_by(questionnaire_id=questionnaire_id).all()
        return render_template('coureur/fill_questionnaire.html', 
                             questionnaire=questionnaire, 
                             participants=participants)
        
    except Exception as e:
        current_app.logger.error(f"Erreur questionnaire: {e}")
        flash('Erreur lors du chargement du questionnaire.', 'danger')
        return redirect(url_for('main.coureur_questionnaires'))

@main_bp.route('/coureur/questionnaire/<int:questionnaire_id>/results')
@coureur_required
def questionnaire_results(questionnaire_id):
    try:
        user_id = session['user_id']
        
        # Vérifier que le coureur est participant à ce questionnaire
        participation = QuestionnaireParticipant.query.filter_by(
            questionnaire_id=questionnaire_id, 
            user_id=user_id
        ).first()
        
        if not participation:
            flash('Vous n\'êtes pas autorisé à voir les résultats de ce questionnaire.', 'danger')
            return redirect(url_for('main.coureur_questionnaires'))
        
        questionnaire = Questionnaire.query.get_or_404(questionnaire_id)
        
        # Récupérer les réponses du coureur
        responses = QuestionnaireResponse.query.filter_by(
            questionnaire_id=questionnaire_id,
            evaluator_id=user_id
        ).all()
        
        # Organiser les données pour l'affichage
        results = []
        for response in responses:
            results.append({
                'evaluated_name': response.evaluated.username,
                'rating': response.rating,
                'created_at': response.created_at
            })
        
        return render_template('coureur/questionnaire_results.html', 
                             questionnaire=questionnaire, 
                             results=results)
        
    except Exception as e:
        current_app.logger.error(f"Erreur résultats questionnaire: {e}")
        flash('Erreur lors du chargement des résultats.', 'danger')
        return redirect(url_for('main.coureur_questionnaires'))

@main_bp.route('/coureur/points-details')
@coureur_required
def coureur_points_details():
    """
    Affiche les détails des points gagnés par course pour le coureur
    """
    try:
        user_id = session['user_id']
        
        # Obtenir la date actuelle et le mois sélectionné
        from datetime import datetime
        now = datetime.utcnow()
        selected_month = request.args.get('month', now.month, type=int)
        selected_year = request.args.get('year', now.year, type=int)
        
        # Calculer la date de début du mois sélectionné
        start_of_selected_month = datetime(selected_year, selected_month, 1)
        start_of_current_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        month_names = [
            "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
            "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
        ]
        selected_month_name = month_names[selected_month - 1]
        current_month_name = month_names[now.month - 1]
        
        # Récupérer toutes les participations du coureur avec les questionnaires
        participations = db.session.query(
            QuestionnaireParticipant, Questionnaire
        ).join(
            Questionnaire, QuestionnaireParticipant.questionnaire_id == Questionnaire.id
        ).filter(
            QuestionnaireParticipant.user_id == user_id
        ).order_by(Questionnaire.course_date.desc()).all()
        
        courses_details = []
        total_note_moyenne = 0
        nb_courses_avec_notes = 0
        total_note_moyenne_mois = 0
        nb_courses_avec_notes_mois = 0
        total_note_moyenne_selected_month = 0
        nb_courses_avec_notes_selected_month = 0
        
        for participation, questionnaire in participations:
            # Vérifier si le coureur a répondu à ce questionnaire
            has_responded = db.session.query(QuestionnaireResponse).filter(
                QuestionnaireResponse.questionnaire_id == questionnaire.id,
                QuestionnaireResponse.evaluated_id == user_id
            ).first() is not None
            
            # Calculer la note moyenne personnelle reçue pour cette course
            note_moyenne_perso = db.session.query(func.avg(QuestionnaireResponse.rating)).filter(
                QuestionnaireResponse.questionnaire_id == questionnaire.id,
                QuestionnaireResponse.evaluated_id == user_id
            ).scalar() or 0
            
            # Calculer la note moyenne équipe pour cette course
            note_moyenne_equipe = db.session.query(func.avg(QuestionnaireResponse.rating)).filter(
                QuestionnaireResponse.questionnaire_id == questionnaire.id
            ).scalar() or 0
            
            # Calculer le nombre de votants pour cette course
            nb_votants = db.session.query(QuestionnaireResponse.evaluator_id).filter(
                QuestionnaireResponse.questionnaire_id == questionnaire.id
            ).distinct().count()
            
            # Accumuler pour le calcul de la moyenne globale
            if float(note_moyenne_perso) > 0:
                total_note_moyenne += float(note_moyenne_perso)
                nb_courses_avec_notes += 1
                
                # Accumuler pour le calcul de la moyenne du mois actuel
                if questionnaire.course_date >= start_of_current_month.date():
                    total_note_moyenne_mois += float(note_moyenne_perso)
                    nb_courses_avec_notes_mois += 1
                
                # Accumuler pour le calcul de la moyenne du mois sélectionné
                if (questionnaire.course_date.year == selected_year and 
                    questionnaire.course_date.month == selected_month):
                    total_note_moyenne_selected_month += float(note_moyenne_perso)
                    nb_courses_avec_notes_selected_month += 1
            
            courses_details.append({
                'course_name': questionnaire.course_name,
                'course_date': questionnaire.course_date,
                'direct_velo_points': questionnaire.direct_velo_points,
                'note_moyenne_perso': round(float(note_moyenne_perso), 1),
                'note_moyenne_equipe': round(float(note_moyenne_equipe), 1),
                'nb_votants': nb_votants,
                'has_responded': has_responded
            })
        
        # Calculer les notes moyennes
        note_moyenne_globale = round(total_note_moyenne / nb_courses_avec_notes, 1) if nb_courses_avec_notes > 0 else 0
        note_moyenne_mois = round(total_note_moyenne_mois / nb_courses_avec_notes_mois, 1) if nb_courses_avec_notes_mois > 0 else 0
        note_moyenne_selected_month = round(total_note_moyenne_selected_month / nb_courses_avec_notes_selected_month, 1) if nb_courses_avec_notes_selected_month > 0 else 0
        
        # Générer les options de mois pour le sélecteur (saison de novembre à novembre)
        month_options = []
        current_year = now.year
        current_month = now.month
        
        # Déterminer la saison actuelle
        if current_month >= 11:  # Novembre ou décembre
            season_start_year = current_year
        else:
            season_start_year = current_year - 1
        
        # Générer les mois de la saison (novembre à novembre)
        for year in [season_start_year, season_start_year + 1]:
            start_month = 11 if year == season_start_year else 1
            end_month = 12 if year == season_start_year else 10
            
            for month in range(start_month, end_month + 1):
                # Ne pas inclure les mois futurs
                if year == current_year and month > current_month:
                    continue
                    
                month_options.append({
                    'value': f"{year}-{month:02d}",
                    'label': f"{month_names[month-1]} {year}",
                    'selected': year == selected_year and month == selected_month
                })
        
        return render_template('coureur/points_details.html', 
                             courses_details=courses_details,
                             note_moyenne_globale=note_moyenne_globale,
                             note_moyenne_mois=note_moyenne_mois,
                             note_moyenne_selected_month=note_moyenne_selected_month,
                             current_month_name=current_month_name,
                             selected_month_name=selected_month_name,
                             month_options=month_options,
                             selected_month=selected_month,
                             selected_year=selected_year)
        
    except Exception as e:
        current_app.logger.error(f"Erreur détails points: {e}")
        flash('Erreur lors du chargement des détails des points.', 'danger')
        return redirect(url_for('main.coureur_dashboard'))

@main_bp.route('/admin/questionnaires')
@admin_required
def admin_questionnaires():
    """
    Affiche tous les questionnaires créés et les statistiques de réponses pour les admins
    """
    try:
        # Récupérer tous les questionnaires avec les statistiques
        questionnaires = db.session.query(
            Questionnaire,
            func.count(QuestionnaireParticipant.user_id).label('nb_participants'),
            func.sum(case((QuestionnaireParticipant.has_responded == True, 1), else_=0)).label('nb_reponses')
        ).outerjoin(
            QuestionnaireParticipant, Questionnaire.id == QuestionnaireParticipant.questionnaire_id
        ).group_by(
            Questionnaire.id
        ).order_by(Questionnaire.course_date.desc()).all()
        
        questionnaires_details = []
        
        for questionnaire, nb_participants, nb_reponses in questionnaires:
            # Calculer le taux de réponse
            taux_reponse = 0
            if nb_participants > 0:
                taux_reponse = round((nb_reponses / nb_participants) * 100, 1)
            
            # Récupérer les participants
            participants = db.session.query(
                User.username,
                QuestionnaireParticipant.has_responded,
                QuestionnaireParticipant.response_date
            ).join(
                QuestionnaireParticipant, User.id == QuestionnaireParticipant.user_id
            ).filter(
                QuestionnaireParticipant.questionnaire_id == questionnaire.id
            ).all()
            
            questionnaires_details.append({
                'id': questionnaire.id,
                'course_name': questionnaire.course_name,
                'course_date': questionnaire.course_date,
                'direct_velo_points': questionnaire.direct_velo_points,
                'created_at': questionnaire.created_at,
                'nb_participants': nb_participants,
                'nb_reponses': nb_reponses,
                'taux_reponse': taux_reponse,
                'participants': participants
            })
        
        return render_template('admin/questionnaires.html', questionnaires=questionnaires_details)
        
    except Exception as e:
        current_app.logger.error(f"Erreur questionnaires admin: {e}")
        flash('Erreur lors du chargement des questionnaires.', 'danger')
        return redirect(url_for('main.admin_dashboard'))

@main_bp.route('/admin/questionnaire/<int:questionnaire_id>/results')
@admin_required
def admin_questionnaire_results(questionnaire_id):
    """
    Affiche les résultats détaillés d'un questionnaire pour l'admin
    """
    try:
        # Récupérer le questionnaire
        questionnaire = Questionnaire.query.get_or_404(questionnaire_id)
        
        # Récupérer tous les participants avec leurs IDs
        participants = db.session.query(
            User.id,
            User.username,
            QuestionnaireParticipant.has_responded,
            QuestionnaireParticipant.response_date
        ).join(
            QuestionnaireParticipant, User.id == QuestionnaireParticipant.user_id
        ).filter(
            QuestionnaireParticipant.questionnaire_id == questionnaire_id
        ).all()
        
        # Récupérer toutes les réponses pour ce questionnaire
        all_responses = db.session.query(
            QuestionnaireResponse.evaluator_id,
            QuestionnaireResponse.evaluated_id,
            QuestionnaireResponse.rating,
            User.username.label('evaluator_name'),
            User.username.label('evaluated_name')
        ).join(
            User, QuestionnaireResponse.evaluator_id == User.id
        ).filter(
            QuestionnaireResponse.questionnaire_id == questionnaire_id
        ).all()
        
        # Organiser les données pour l'affichage
        results_data = []
        for participant in participants:
            user_id = participant.id
            username = participant.username
            
            # Récupérer les notes données par ce participant
            participant_responses = []
            for response in all_responses:
                if response.evaluator_id == user_id:
                    participant_responses.append({
                        'evaluated_name': response.evaluated_name,
                        'rating': response.rating
                    })
            
            # Récupérer les notes reçues par ce participant
            received_ratings = []
            for response in all_responses:
                if response.evaluated_id == user_id:
                    received_ratings.append(response.rating)
            
            # Calculer la note moyenne reçue
            avg_rating_received = 0
            if received_ratings:
                avg_rating_received = sum(received_ratings) / len(received_ratings)
            
            results_data.append({
                'username': username,
                'has_responded': participant.has_responded,
                'response_date': participant.response_date,
                'responses_given': participant_responses,
                'avg_rating_received': round(avg_rating_received, 1),
                'nb_ratings_received': len(received_ratings)
            })
        
        return render_template('admin/questionnaire_results.html', 
                             questionnaire=questionnaire,
                             results=results_data)
        
    except Exception as e:
        current_app.logger.error(f"Erreur résultats questionnaire admin: {e}")
        flash('Erreur lors du chargement des résultats.', 'danger')
        return redirect(url_for('main.admin_questionnaires'))

@main_bp.route('/debug-ranking')
@login_required
def debug_ranking():
    """Route de debug pour tester le calcul du classement"""
    try:
        user_id = session['user_id']
        user = User.query.get(user_id)
        
        # Calculer le classement
        classement_mois, classement_annee = calculate_coureur_ranking(user_id)
        
        # Récupérer toutes les participations du coureur pour debug
        participations = db.session.query(
            QuestionnaireParticipant, Questionnaire
        ).join(
            Questionnaire, QuestionnaireParticipant.questionnaire_id == Questionnaire.id
        ).filter(
            QuestionnaireParticipant.user_id == user_id
        ).all()
        
        debug_data = []
        total_points = 0
        
        for participation, questionnaire in participations:
            # Calculer la note moyenne reçue pour cette course
            avg_rating = db.session.query(func.avg(QuestionnaireResponse.rating)).filter(
                QuestionnaireResponse.questionnaire_id == questionnaire.id,
                QuestionnaireResponse.evaluated_id == user_id
            ).scalar() or 0
            
            # Calculer les points pour cette course
            course_points = questionnaire.direct_velo_points * float(avg_rating)
            total_points += course_points
            
            debug_data.append({
                'course_name': questionnaire.course_name,
                'course_date': questionnaire.course_date,
                'direct_velo_points': questionnaire.direct_velo_points,
                'avg_rating': float(avg_rating),
                'course_points': course_points,
                'has_responded': participation.has_responded
            })
        
        debug_html = f"""
        <h2>Debug Classement - {user.username}</h2>
        <p><strong>Classement du mois:</strong> {classement_mois}</p>
        <p><strong>Classement de l'année:</strong> {classement_annee}</p>
        <p><strong>Total des points:</strong> {round(total_points, 1)}</p>
        
        <h3>Détail des courses:</h3>
        <table border="1" style="border-collapse: collapse; width: 100%;">
            <tr>
                <th>Course</th>
                <th>Date</th>
                <th>Points Direct Vélo</th>
                <th>Note moyenne</th>
                <th>Points gagnés</th>
                <th>Répondu</th>
            </tr>
        """
        
        for data in debug_data:
            debug_html += f"""
            <tr>
                <td>{data['course_name']}</td>
                <td>{data['course_date']}</td>
                <td>{data['direct_velo_points']}</td>
                <td>{data['avg_rating']}</td>
                <td>{data['course_points']}</td>
                <td>{'Oui' if data['has_responded'] else 'Non'}</td>
            </tr>
            """
        
        debug_html += """
        </table>
        
        <br><br>
        <a href="/coureur/dashboard" style="background: blue; color: white; padding: 10px; text-decoration: none;">Retour au Dashboard</a>
        """
        
        return debug_html
        
    except Exception as e:
        return f"Erreur debug: {e}"

@main_bp.route('/coureur/rankings')
@coureur_required
def coureur_rankings():
    """
    Affiche les classements du mois et de l'année
    """
    try:
        from datetime import datetime
        from sqlalchemy import func
        
        # Obtenir la date actuelle et le mois sélectionné
        now = datetime.utcnow()
        selected_month = request.args.get('month', now.month, type=int)
        selected_year = request.args.get('year', now.year, type=int)
        
        # Calculer la date de début du mois sélectionné
        start_of_selected_month = datetime(selected_year, selected_month, 1)
        start_of_current_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_of_year = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Récupérer tous les coureurs
        all_coureurs = User.query.filter_by(role='coureur', is_active=True).all()
        
        # Calculer la période de la saison (novembre à octobre)
        # Trouver la saison correspondant au mois sélectionné
        if selected_month >= 11:
            season_start_year = selected_year
            season_end_year = selected_year + 1
        else:
            season_start_year = selected_year - 1
            season_end_year = selected_year
        season_start_date = datetime(season_start_year, 11, 1).date()
        season_end_date = datetime(season_end_year, 10, 31).date()

        # Calculer les points pour tous les coureurs
        coureurs_rankings = []
        for coureur in all_coureurs:
            participations = db.session.query(
                QuestionnaireParticipant, Questionnaire
            ).join(
                Questionnaire, QuestionnaireParticipant.questionnaire_id == Questionnaire.id
            ).filter(
                QuestionnaireParticipant.user_id == coureur.id
            ).all()

            season_points = 0
            monthly_points = 0
            selected_month_points = 0

            for participation, questionnaire in participations:
                avg_rating = db.session.query(func.avg(QuestionnaireResponse.rating)).filter(
                    QuestionnaireResponse.questionnaire_id == questionnaire.id,
                    QuestionnaireResponse.evaluated_id == coureur.id
                ).scalar() or 0
                course_points = questionnaire.direct_velo_points * float(avg_rating)

                # Ajouter aux points de la saison
                if season_start_date <= questionnaire.course_date <= season_end_date:
                    season_points += course_points
                # Ajouter aux points du mois actuel
                if questionnaire.course_date >= start_of_current_month.date():
                    monthly_points += course_points
                # Ajouter aux points du mois sélectionné
                if (questionnaire.course_date.year == selected_year and 
                    questionnaire.course_date.month == selected_month):
                    selected_month_points += course_points

            coureurs_rankings.append({
                'user_id': coureur.id,
                'username': coureur.username,
                'season_points': round(season_points, 1),
                'monthly_points': round(monthly_points, 1),
                'selected_month_points': round(selected_month_points, 1)
            })

        # Trier par points de la saison décroissants
        season_rankings = sorted(coureurs_rankings, key=lambda x: x['season_points'], reverse=True)
        # Trier par points du mois sélectionné décroissants
        selected_month_rankings = sorted(coureurs_rankings, key=lambda x: x['selected_month_points'], reverse=True)

        # Obtenir le nom du mois sélectionné
        month_names = [
            "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
            "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
        ]
        selected_month_name = month_names[selected_month - 1]
        current_month_name = month_names[now.month - 1]
        
        # Générer les options de mois pour le sélecteur (saison de novembre à novembre)
        month_options = []
        current_year = now.year
        current_month = now.month
        
        # Déterminer la saison actuelle
        # Si on est entre novembre et décembre, c'est la saison en cours
        # Sinon, c'est la saison précédente
        if current_month >= 11:  # Novembre ou décembre
            season_start_year = current_year
        else:
            season_start_year = current_year - 1
        
        # Correction : définir la saison courante
        current_season = (now.year if now.month < 11 else now.year + 1)

        # Générer les mois de la saison (novembre à novembre)
        for year in [season_start_year, season_start_year + 1]:
            start_month = 11 if year == season_start_year else 1
            end_month = 12 if year == season_start_year else 10
            
            for month in range(start_month, end_month + 1):
                # Ne pas inclure les mois futurs SEULEMENT si saison en cours
                if (season_start_year + 1 == current_season) and (year == now.year and month > now.month):
                    continue
                month_options.append({
                    'value': f"{year}-{month:02d}",
                    'label': f"{month_names[month-1]} {year}",
                    'selected': year == selected_year and month == selected_month
                })
        
        return render_template('coureur/rankings.html', 
                             season_rankings=season_rankings,
                             selected_month_rankings=selected_month_rankings,
                             selected_month_name=selected_month_name,
                             current_month_name=current_month_name,
                             month_options=month_options,
                             selected_month=selected_month,
                             selected_year=selected_year)
        
    except Exception as e:
        current_app.logger.error(f"Erreur classements: {e}")
        flash('Erreur lors du chargement des classements.', 'danger')
        return redirect(url_for('main.coureur_dashboard'))

@main_bp.route('/admin/course-statistics')
@admin_required
def admin_course_statistics():
    """
    Affiche les statistiques des courses avec les notes moyennes et points de chaque coureur
    """
    try:
        from sqlalchemy import func
        from datetime import datetime
        
        # Obtenir la date actuelle et les paramètres sélectionnés
        now = datetime.utcnow()
        selected_month = request.args.get('month', now.month, type=int)
        selected_year = request.args.get('year', now.year, type=int)
        selected_season = request.args.get('season', now.year, type=int)
        
        # Debug: afficher les paramètres reçus
        current_app.logger.info(f"Paramètres reçus: month={selected_month}, year={selected_year}, season={selected_season}")
        
        # Si une nouvelle saison est sélectionnée, ajuster le mois et l'année
        if 'season' in request.args and 'month' not in request.args:
            # Pour la saison sélectionnée, commencer par novembre de l'année précédente
            season_start_year = selected_season - 1
            # Si on est dans la saison actuelle, utiliser le mois actuel, sinon novembre
            if selected_season == now.year:
                selected_month = now.month
                selected_year = now.year
            else:
                selected_month = 11  # Novembre
                selected_year = season_start_year
        
        # Récupérer les questionnaires du mois sélectionné
        questionnaires = Questionnaire.query.filter(
            Questionnaire.course_date >= datetime(selected_year, selected_month, 1).date(),
            Questionnaire.course_date < datetime(selected_year, selected_month + 1, 1).date() if selected_month < 12 
            else datetime(selected_year + 1, 1, 1).date()
        ).order_by(Questionnaire.course_date.desc()).all()
        
        # Pour chaque questionnaire, calculer les statistiques
        course_stats = []
        
        for questionnaire in questionnaires:
            # Récupérer tous les participants de ce questionnaire
            participants = db.session.query(
                User.id,
                User.username,
                QuestionnaireParticipant.has_responded
            ).join(
                QuestionnaireParticipant, User.id == QuestionnaireParticipant.user_id
            ).filter(
                QuestionnaireParticipant.questionnaire_id == questionnaire.id
            ).all()
            
            # Calculer les statistiques pour chaque participant
            participant_stats = []
            all_ratings = []
            
            for participant in participants:
                user_id = participant.id
                
                # Récupérer les notes reçues par ce participant
                received_ratings = db.session.query(QuestionnaireResponse.rating).filter(
                    QuestionnaireResponse.questionnaire_id == questionnaire.id,
                    QuestionnaireResponse.evaluated_id == user_id
                ).all()
                
                # Calculer la note moyenne, mini et maxi
                avg_rating = 0
                min_rating = None
                max_rating = None
                if received_ratings:
                    ratings = [r.rating for r in received_ratings]
                    avg_rating = sum(ratings) / len(ratings)
                    min_rating = min(ratings)
                    max_rating = max(ratings)
                    all_ratings.extend(ratings)
                
                # Calculer les points (note moyenne x points direct vélo)
                points = avg_rating * questionnaire.direct_velo_points
                
                participant_stats.append({
                    'username': participant.username,
                    'avg_rating': round(avg_rating, 1),
                    'min_rating': min_rating,
                    'max_rating': max_rating,
                    'points': round(points, 1)
                })
            
            # Calculer la note moyenne de l'équipe
            team_avg_rating = 0
            if all_ratings:
                team_avg_rating = sum(all_ratings) / len(all_ratings)
            
            course_stats.append({
                'questionnaire': questionnaire,
                'participants': participant_stats,
                'team_avg_rating': round(team_avg_rating, 1),
                'nb_participants': len(participants)
            })
        
        # S'assurer que la variable 'season' est toujours définie et cohérente AVANT toute utilisation
        try:
            season = int(selected_season)
        except (TypeError, ValueError):
            if now.month >= 11:
                season = now.year + 1
            else:
                season = now.year
        
        # Générer la liste des saisons pour la dropdown (après avoir déterminé la saison sélectionnée)
        season_options = []
        if 'available_seasons' not in locals():
            all_course_dates = db.session.query(Questionnaire.course_date).distinct().all()
            available_seasons = set()
            for course_date in all_course_dates:
                course_year = course_date[0].year
                course_month = course_date[0].month
                if course_month >= 11:
                    season_val = course_year + 1
                else:
                    season_val = course_year
                available_seasons.add(season_val)
        for s in sorted(available_seasons, reverse=True):
            season_options.append({'year': s, 'selected': s == season})
        
        # Générer les options de mois pour la saison sélectionnée
        month_options = []
        season_start_year = season - 1
        # Générer les mois de la saison (novembre à octobre)
        for year in [season_start_year, season]:
            start_month = 11 if year == season_start_year else 1
            end_month = 12 if year == season_start_year else 10
            for month in range(start_month, end_month + 1):
                # Ne pas inclure les mois futurs SEULEMENT si saison en cours
                if (season == (now.year if now.month < 11 else now.year+1)) and (year == now.year and month > now.month):
                    continue
                month_options.append({
                    'year': year,
                    'month': month,
                    'selected': year == selected_year and month == selected_month
                })
        
        # Obtenir le nom du mois sélectionné
        month_names = [
            "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
            "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
        ]
        selected_month_name = month_names[selected_month - 1]
        
        return render_template('admin/course_statistics.html', 
                             course_stats=course_stats,
                             month_options=month_options,
                             season_options=season_options,
                             selected_month_name=selected_month_name,
                             selected_month=selected_month,
                             selected_year=selected_year,
                             selected_season=selected_season)
        
    except Exception as e:
        current_app.logger.error(f"Erreur statistiques courses admin: {e}")
        flash('Erreur lors du chargement des statistiques.', 'danger')
        return redirect(url_for('main.admin_dashboard'))

@main_bp.route('/admin/global-rankings')
@admin_required
def admin_global_rankings():
    """
    Affiche le classement global de la saison en cours, du mois en cours et des mois précédents (sélection via liste déroulante)
    """
    from datetime import datetime
    from sqlalchemy import func
    now = datetime.utcnow()
    # Générer la liste des saisons disponibles (celles où il y a au moins une course)
    all_course_dates = db.session.query(Questionnaire.course_date).distinct().all()
    available_seasons = set()
    for course_date in all_course_dates:
        course_year = course_date[0].year
        course_month = course_date[0].month
        if course_month >= 11:
            season_val = course_year + 1
        else:
            season_val = course_year
        available_seasons.add(season_val)
    # Détermination de la saison sélectionnée (GET ou défaut)
    selected_season = request.args.get('season', type=int)
    if selected_season:
        season = selected_season
    else:
        if now.month >= 11:
            season = now.year + 1
        else:
            season = now.year
    # Calcul des bornes de la saison sélectionnée
    season_start = datetime(season - 1, 11, 1)
    season_end = datetime(season, 10, 31, 23, 59, 59)
    # Liste des mois de la saison sélectionnée
    months = []
    for y in [season-1, season]:
        start = 11 if y == season-1 else 1
        end = 12 if y == season-1 else 10
        for m in range(start, end+1):
            # Ne pas inclure les mois futurs SEULEMENT si saison en cours
            if (season == (now.year if now.month < 11 else now.year+1)) and (y == now.year and m > now.month):
                continue
            months.append({'year': y, 'month': m})
    # Mois sélectionné (par défaut mois en cours)
    selected_month = int(request.args.get('month', now.month))
    selected_year = int(request.args.get('year', now.year))
    # Classement du mois sélectionné
    month_start = datetime(selected_year, selected_month, 1)
    if selected_month < 12:
        month_end = datetime(selected_year, selected_month+1, 1)
    else:
        month_end = datetime(selected_year+1, 1, 1)
    # Récupérer tous les coureurs actifs
    coureurs = User.query.filter_by(role='coureur', is_active=True).all()
    # Classement saison
    saison_points = []
    for coureur in coureurs:
        participations = db.session.query(QuestionnaireParticipant, Questionnaire).join(
            Questionnaire, QuestionnaireParticipant.questionnaire_id == Questionnaire.id
        ).filter(
            QuestionnaireParticipant.user_id == coureur.id,
            Questionnaire.course_date >= season_start.date(),
            Questionnaire.course_date <= season_end.date()
        ).all()
        total_points = 0
        for participation, questionnaire in participations:
            avg_rating = db.session.query(func.avg(QuestionnaireResponse.rating)).filter(
                QuestionnaireResponse.questionnaire_id == questionnaire.id,
                QuestionnaireResponse.evaluated_id == coureur.id
            ).scalar() or 0
            total_points += questionnaire.direct_velo_points * float(avg_rating)
        saison_points.append({'username': coureur.username, 'points': round(total_points, 1)})
    saison_points.sort(key=lambda x: x['points'], reverse=True)
    # Classement du mois sélectionné
    mois_points = []
    for coureur in coureurs:
        participations = db.session.query(QuestionnaireParticipant, Questionnaire).join(
            Questionnaire, QuestionnaireParticipant.questionnaire_id == Questionnaire.id
        ).filter(
            QuestionnaireParticipant.user_id == coureur.id,
            Questionnaire.course_date >= month_start.date(),
            Questionnaire.course_date < month_end.date()
        ).all()
        total_points = 0
        for participation, questionnaire in participations:
            avg_rating = db.session.query(func.avg(QuestionnaireResponse.rating)).filter(
                QuestionnaireResponse.questionnaire_id == questionnaire.id,
                QuestionnaireResponse.evaluated_id == coureur.id
            ).scalar() or 0
            total_points += questionnaire.direct_velo_points * float(avg_rating)
        mois_points.append({'username': coureur.username, 'points': round(total_points, 1)})
    mois_points.sort(key=lambda x: x['points'], reverse=True)
    # Pour affichage du mois
    month_names = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
    selected_month_name = month_names[selected_month-1]
    # Générer la liste des saisons pour la dropdown (après avoir déterminé la saison sélectionnée)
    season_options = []
    for s in sorted(available_seasons, reverse=True):
        season_options.append({'year': s, 'selected': s == season})
    return render_template('admin/global_rankings.html',
        saison_points=saison_points,
        mois_points=mois_points,
        months=months,
        selected_month=selected_month,
        selected_year=selected_year,
        selected_month_name=selected_month_name,
        season=season,
        season_options=season_options
    )

@main_bp.route('/admin/questionnaire/<int:questionnaire_id>/delete', methods=['POST'])
@admin_required
def delete_questionnaire(questionnaire_id):
    """
    Permet à l'admin de supprimer un questionnaire et toutes ses données associées
    """
    try:
        questionnaire = Questionnaire.query.get_or_404(questionnaire_id)
        db.session.delete(questionnaire)
        db.session.commit()
        flash('Le questionnaire a bien été supprimé.', 'success')
        return redirect(url_for('main.admin_questionnaires'))
    except Exception as e:
        current_app.logger.error(f"Erreur suppression questionnaire: {e}")
        flash("Erreur lors de la suppression du questionnaire.", 'danger')
        return redirect(url_for('main.admin_questionnaire_results', questionnaire_id=questionnaire_id)) 