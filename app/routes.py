from flask import Blueprint, render_template, redirect, url_for, request, flash, session, abort, current_app, send_from_directory, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User, Questionnaire, QuestionnaireParticipant, QuestionnaireResponse, Team
from flask_login import current_user, login_user, login_required
from app import db, mail, serializer
from flask_mail import Message
from itsdangerous import SignatureExpired, BadSignature
from datetime import datetime
from sqlalchemy import func, case
import os

def get_current_date():
    """
    Retourne la date actuelle réelle
    """
    return datetime.utcnow()

main_bp = Blueprint('main', __name__)

month_names = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
]

@main_bp.route('/')
def index():
    user = current_user
    return render_template('index.html')

@main_bp.route('/favicon.ico')
def favicon():
    """Route spéciale pour servir le favicon"""
    user = current_user
    return send_from_directory(os.path.join(os.getcwd(), 'static'), 'favicon.ico')

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    user = current_user
    teams = Team.query.filter_by(actif=True).all()
    if request.method == 'POST':
        prenom = request.form['prenom'].strip()
        nom = request.form['nom'].strip()
        email = request.form['email'].strip().lower()
        telephone = request.form.get('telephone', '').strip()
        notifications_sms = request.form.get('notifications_sms') == 'on'
        password = request.form['password']
        team_id = request.form.get('team_id')
        role = request.form.get('role', 'coureur')
        errors = []
        if not telephone:
            errors.append("Le numéro de téléphone est obligatoire.")
        is_valid_prenom, prenom_msg = User.validate_prenom(prenom)
        if not is_valid_prenom:
            errors.append(prenom_msg)
        is_valid_nom, nom_msg = User.validate_nom(nom)
        if not is_valid_nom:
            errors.append(nom_msg)
        if not User.validate_email(email):
            errors.append("Format d'email invalide")
        is_valid_telephone, telephone_msg = User.validate_telephone(telephone)
        if not is_valid_telephone:
            errors.append(telephone_msg)
        is_valid_password, password_msg = User.validate_password(password)
        if not is_valid_password:
            errors.append(password_msg)
        if role not in ['coureur', 'admin']:
            role = 'coureur'
        if User.query.filter_by(email=email).first():
            errors.append('Email déjà utilisé')
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('register.html', teams=teams)
        try:
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(
                prenom=prenom, 
                nom=nom, 
                email=email, 
                telephone=telephone,
                notifications_sms=notifications_sms,
                password=hashed_password, 
                role=role, 
                team_id=team_id
            )
            db.session.add(new_user)
            db.session.commit()
            flash(f'Votre compte {role} a été créé avec succès!', 'success')
            return redirect(url_for('main.login'))
        except Exception as e:
            db.session.rollback()
            flash('Erreur lors de la création du compte. Veuillez réessayer.', 'danger')
            current_app.logger.error(f"Erreur création utilisateur: {e}")
            return render_template('register.html', teams=teams)
    return render_template('register.html', teams=teams)

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    user = current_user
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password']
        remember = True if request.form.get('remember') else False
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            flash('Veuillez vérifier vos identifiants et réessayer.', 'danger')
            return redirect(url_for('main.login'))
        if not user.is_active:
            flash('Votre compte a été désactivé. Contactez l\'administrateur.', 'danger')
            return redirect(url_for('main.login'))
        try:
            login_user(user, remember=remember)
            current_app.logger.info(f"Connexion réussie: {user.prenom} {user.nom} ({user.role})")
            flash(f'Bienvenue, {user.prenom} {user.nom} ({user.role})!', 'success')
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
    user = current_user
    if user.role == 'admin':
        return redirect(url_for('main.admin_dashboard'))
    else:
        return redirect(url_for('main.coureur_dashboard'))

@main_bp.route('/admin/dashboard')
@login_required
def admin_dashboard():
    user = current_user
    if not user.is_admin():
        flash('Accès interdit. Privilèges administrateur requis.', 'danger')
        return redirect(url_for('main.dashboard'))
    try:
        total_users = User.query.count()
        total_coureurs = User.query.filter_by(role='coureur', is_active=True).count()
        total_admins = User.query.filter_by(role='admin').count()
        active_users = User.query.filter_by(is_active=True).count()
        inactive_users = User.query.filter_by(is_active=False).count()
        all_users = User.query.order_by(User.created_at.desc()).all()
        coureurs_sans_equipe = User.query.filter_by(role='coureur', is_active=True, team_id=None).order_by(User.nom, User.prenom).all()
        all_coureurs = User.query.filter_by(role='coureur', is_active=True, team_id=None).order_by(User.nom, User.prenom).all()
        stats = {
            'total_users': total_users,
            'total_coureurs': total_coureurs,
            'total_admins': total_admins,
            'active_users': active_users,
            'inactive_users': inactive_users
        }
        return render_template('admin/dashboard.html', username=user.prenom + ' ' + user.nom, current_user=user, all_users=all_users, stats=stats, all_coureurs=all_coureurs, coureurs_sans_equipe=coureurs_sans_equipe)
    except Exception as e:
        current_app.logger.error(f"Erreur dashboard admin: {e}")
        flash('Erreur lors du chargement du dashboard.', 'danger')
        return redirect(url_for('main.dashboard'))

@main_bp.route('/admin/users')
@login_required
def admin_users():
    user = current_user
    if not user.is_admin():
        flash('Accès interdit. Privilèges administrateur requis.', 'danger')
        return redirect(url_for('main.dashboard'))
    try:
        team_id = request.args.get('team_id', type=int)
        if team_id:
            users = User.query.filter_by(team_id=team_id).order_by(User.created_at.desc()).all()
        else:
            users = User.query.order_by(User.created_at.desc()).all()
        current_user_id = user.id
        teams = Team.query.filter_by(actif=True).all()
        return render_template('admin/users.html', users=users, current_user_id=current_user_id, teams=teams)
    except Exception as e:
        current_app.logger.error(f"Erreur liste utilisateurs: {e}")
        flash('Erreur lors du chargement des utilisateurs.', 'danger')
        return redirect(url_for('main.admin_dashboard'))

@main_bp.route('/admin/users/export-csv')
@login_required
def export_users_csv():
    user = current_user
    if not user.is_admin():
        flash('Accès interdit. Privilèges administrateur requis.', 'danger')
        return redirect(url_for('main.dashboard'))
    try:
        from io import StringIO
        import csv
        from flask import Response
        
        # Vérifier si c'est un template d'import (pas d'utilisateurs existants)
        template_mode = request.args.get('template', 'false').lower() == 'true'
        
        if template_mode:
            # Créer un template d'import
            output = StringIO()
            writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_ALL)
            
            # En-têtes pour l'import
            writer.writerow([
                'prenom', 'nom', 'email', 'telephone', 'role', 'equipe', 'notifications_sms'
            ])
            
            # Exemples de données
            writer.writerow([
                'Jean', 'Dupont', 'jean.dupont@email.com', '0123456789', 'coureur', 'Équipe A', 'true'
            ])
            writer.writerow([
                'Marie', 'Martin', 'marie.martin@email.com', '0987654321', 'admin', '', 'false'
            ])
            
            output.seek(0)
            csv_content = output.getvalue()
            
            response = Response(csv_content, mimetype='text/csv; charset=utf-8')
            response.headers['Content-Disposition'] = 'attachment; filename=template_import_utilisateurs.csv'
            
            return response
        else:
            # Export normal des utilisateurs existants
            users = User.query.order_by(User.nom, User.prenom).all()
            
            # Créer le contenu CSV
            output = StringIO()
            writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_ALL)
            
            # En-têtes
            writer.writerow([
                'ID', 'Prénom', 'Nom', 'Email', 'Téléphone', 'Rôle', 
                'Statut', 'Équipe', 'Notifications SMS', 'Date de création'
            ])
            
            # Données des utilisateurs
            for user in users:
                team_name = user.team.nom if user.team else 'Aucune équipe'
                status = 'Actif' if user.is_active else 'Inactif'
                notifications = 'Oui' if user.notifications_sms else 'Non'
                created_date = user.created_at.strftime('%d/%m/%Y %H:%M') if user.created_at else ''
                
                writer.writerow([
                    user.id,
                    user.prenom,
                    user.nom,
                    user.email,
                    user.telephone or '',
                    user.role,
                    status,
                    team_name,
                    notifications,
                    created_date
                ])
            
            # Préparer la réponse
            output.seek(0)
            csv_content = output.getvalue()
            
            # Créer la réponse avec les headers appropriés
            response = Response(csv_content, mimetype='text/csv; charset=utf-8')
            response.headers['Content-Disposition'] = 'attachment; filename=utilisateurs_export.csv'
            
            return response
        
    except Exception as e:
        current_app.logger.error(f"Erreur export CSV utilisateurs: {e}")
        flash('Erreur lors de l\'export CSV.', 'danger')
        return redirect(url_for('main.admin_users'))

@main_bp.route('/admin/users/import-csv', methods=['GET', 'POST'])
@login_required
def import_users_csv():
    user = current_user
    if not user.is_admin():
        flash('Accès interdit. Privilèges administrateur requis.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        try:
            if 'csv_file' not in request.files:
                flash('Aucun fichier sélectionné.', 'danger')
                return render_template('admin/import_users.html')
            
            file = request.files['csv_file']
            if file.filename == '':
                flash('Aucun fichier sélectionné.', 'danger')
                return render_template('admin/import_users.html')
            
            if not file.filename.endswith('.csv'):
                flash('Le fichier doit être au format CSV.', 'danger')
                return render_template('admin/import_users.html')
            
            # Lire le fichier CSV
            import csv
            from io import StringIO
            
            # Lire le contenu du fichier
            content = file.read().decode('utf-8')
            csv_reader = csv.DictReader(StringIO(content), delimiter=';')
            
            # Options d'import
            default_role = request.form.get('default_role', 'coureur')
            skip_duplicates = request.form.get('skip_duplicates') == 'on'
            send_notifications = request.form.get('send_notifications') == 'on'
            
            # Résultats de l'import
            import_results = {
                'success': [],
                'errors': [],
                'skipped': [],
                'success_count': 0,
                'error_count': 0,
                'skipped_count': 0,
                'total_count': 0
            }
            
            # Traiter chaque ligne
            for line_num, row in enumerate(csv_reader, start=2):  # Commencer à 2 car ligne 1 = en-têtes
                import_results['total_count'] += 1
                
                try:
                    # Validation des champs obligatoires
                    if not row.get('prenom') or not row.get('nom') or not row.get('email'):
                        import_results['errors'].append({
                            'line': line_num,
                            'email': row.get('email', 'N/A'),
                            'message': 'Prénom, nom et email sont obligatoires'
                        })
                        import_results['error_count'] += 1
                        continue
                    
                    # Nettoyer les données
                    prenom = row['prenom'].strip()
                    nom = row['nom'].strip()
                    email = row['email'].strip().lower()
                    telephone = row.get('telephone', '').strip()
                    role = row.get('role', default_role).strip()
                    equipe_nom = row.get('equipe', '').strip()
                    notifications_sms = row.get('notifications_sms', str(send_notifications)).strip().lower()
                    
                    # Validation du format email
                    if not User.validate_email(email):
                        import_results['errors'].append({
                            'line': line_num,
                            'email': email,
                            'message': 'Format d\'email invalide'
                        })
                        import_results['error_count'] += 1
                        continue
                    
                    # Validation du téléphone
                    if telephone:
                        is_valid_telephone, telephone_msg = User.validate_telephone(telephone)
                        if not is_valid_telephone:
                            import_results['errors'].append({
                                'line': line_num,
                                'email': email,
                                'message': telephone_msg
                            })
                            import_results['error_count'] += 1
                            continue
                    
                    # Validation du rôle
                    if role not in ['coureur', 'admin']:
                        role = default_role
                    
                    # Vérifier si l'email existe déjà
                    existing_user = User.query.filter_by(email=email).first()
                    if existing_user:
                        if skip_duplicates:
                            import_results['skipped'].append({
                                'line': line_num,
                                'email': email,
                                'message': 'Email déjà existant'
                            })
                            import_results['skipped_count'] += 1
                            continue
                        else:
                            import_results['errors'].append({
                                'line': line_num,
                                'email': email,
                                'message': 'Email déjà existant'
                            })
                            import_results['error_count'] += 1
                            continue
                    
                    # Trouver l'équipe si spécifiée
                    team_id = None
                    if equipe_nom:
                        team = Team.query.filter_by(nom=equipe_nom, actif=True).first()
                        if team:
                            team_id = team.id
                    
                    # Convertir notifications_sms en booléen
                    notifications_bool = notifications_sms in ['true', '1', 'oui', 'yes', 'on']
                    
                    # Créer l'utilisateur
                    new_user = User(
                        prenom=prenom,
                        nom=nom,
                        email=email,
                        telephone=telephone,
                        notifications_sms=notifications_bool,
                        password=generate_password_hash('changeme123', method='pbkdf2:sha256'),  # Mot de passe temporaire
                        role=role,
                        team_id=team_id
                    )
                    
                    db.session.add(new_user)
                    db.session.flush()  # Pour obtenir l'ID
                    
                    import_results['success'].append({
                        'prenom': prenom,
                        'nom': nom,
                        'email': email,
                        'role': role
                    })
                    import_results['success_count'] += 1
                    
                except Exception as e:
                    import_results['errors'].append({
                        'line': line_num,
                        'email': row.get('email', 'N/A'),
                        'message': f'Erreur: {str(e)}'
                    })
                    import_results['error_count'] += 1
                    continue
            
            # Commit final
            db.session.commit()
            
            # Message de succès
            if import_results['success_count'] > 0:
                flash(f'{import_results["success_count"]} utilisateur(s) importé(s) avec succès !', 'success')
            if import_results['error_count'] > 0:
                flash(f'{import_results["error_count"]} erreur(s) lors de l\'import.', 'warning')
            if import_results['skipped_count'] > 0:
                flash(f'{import_results["skipped_count"]} utilisateur(s) ignoré(s) (doublons).', 'info')
            
            return render_template('admin/import_users.html', import_results=import_results)
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur import CSV utilisateurs: {e}")
            flash(f'Erreur lors de l\'import CSV: {str(e)}', 'danger')
            return render_template('admin/import_users.html')
    
    return render_template('admin/import_users.html')

@main_bp.route('/admin/users/<int:user_id>/edit', methods=['POST'])
@login_required
def edit_user(user_id):
    user = current_user
    if not user.is_admin():
        flash('Accès interdit. Privilèges administrateur requis.', 'danger')
        return redirect(url_for('main.dashboard'))
    try:
        user_to_edit = User.query.get_or_404(user_id)
        team_id = request.form.get('team_id')
        if team_id:
            user_to_edit.team_id = int(team_id)
            db.session.commit()
            flash('Équipe modifiée avec succès.', 'success')
        else:
            flash('Aucune équipe sélectionnée.', 'danger')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur modification équipe utilisateur: {e}")
        flash('Erreur lors de la modification de l\'équipe.', 'danger')
    return redirect(url_for('main.admin_users'))

@main_bp.route('/admin/users/<int:user_id>/toggle', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    user = current_user
    if not user.is_admin():
        flash('Accès interdit. Privilèges administrateur requis.', 'danger')
        return redirect(url_for('main.dashboard'))
    try:
        user_to_toggle = User.query.get_or_404(user_id)
        if user_to_toggle.id == current_user.id:
            flash('Vous ne pouvez pas désactiver votre propre compte.', 'warning')
            return redirect(url_for('main.admin_users'))
        user_to_toggle.is_active = not user_to_toggle.is_active
        db.session.commit()
        status = 'activé' if user_to_toggle.is_active else 'désactivé'
        flash(f'Le compte de {user_to_toggle.prenom} {user_to_toggle.nom} a été {status}.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur toggle user status: {e}")
        flash('Erreur lors de la modification du statut.', 'danger')
    return redirect(url_for('main.admin_users'))

@main_bp.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    user = current_user
    try:
        if not user.is_authenticated:
            return redirect(url_for('main.login'))
        user = User.query.get_or_404(user_id)
        if user.id == current_user.id:
            flash('Vous ne pouvez pas supprimer votre propre compte.', 'warning')
            return redirect(url_for('main.admin_users'))
        username = user.prenom + ' ' + user.nom
        db.session.delete(user)
        db.session.commit()
        flash(f'Le compte de {username} a été supprimé.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur suppression utilisateur: {e}")
        flash('Erreur lors de la suppression.', 'danger')
    return redirect(url_for('main.admin_users'))

@main_bp.route('/admin/users/<int:user_id>/promote', methods=['POST'])
@login_required
def promote_user(user_id):
    user = current_user
    try:
        if not user.is_authenticated:
            return redirect(url_for('main.login'))
        user = User.query.get_or_404(user_id)
        if user.role == 'coureur':
            user.role = 'admin'
            db.session.commit()
            flash(f'{user.prenom} {user.nom} a été promu administrateur.', 'success')
        else:
            flash(f'{user.prenom} {user.nom} est déjà administrateur.', 'info')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur promotion utilisateur: {e}")
        flash('Erreur lors de la promotion.', 'danger')
    return redirect(url_for('main.admin_users'))

@main_bp.route('/admin/users/<int:user_id>/demote', methods=['POST'])
@login_required
def demote_user(user_id):
    user = current_user
    try:
        if not user.is_authenticated:
            return redirect(url_for('main.login'))
        user = User.query.get_or_404(user_id)
        if user.id == current_user.id:
            flash('Vous ne pouvez pas modifier votre propre rôle.', 'warning')
            return redirect(url_for('main.admin_users'))
        if user.role == 'admin':
            user.role = 'coureur'
            db.session.commit()
            flash(f'{user.prenom} {user.nom} a été rétrogradé en coureur.', 'success')
        else:
            flash(f'{user.prenom} {user.nom} est déjà coureur.', 'info')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur rétrogradation utilisateur: {e}")
        flash('Erreur lors de la rétrogradation.', 'danger')
    return redirect(url_for('main.admin_users'))

@main_bp.route('/admin/create-questionnaire', methods=['GET', 'POST'])
@login_required
def create_questionnaire():
    user = current_user
    from app.models import Team
    equipes = Team.query.filter_by(actif=True).order_by(Team.nom).all()
    team_id = request.args.get('team_id') or request.form.get('team_id')
    coureurs = []
    if team_id:
        coureurs = User.query.filter_by(role='coureur', is_active=True, team_id=team_id).order_by(User.nom).all()
    if request.method == 'POST' and 'course_name' in request.form:
        try:
            # Récupération des données du formulaire
            course_name = request.form.get('course_name', '').strip()
            course_date = request.form.get('course_date', '')
            direct_velo_points = request.form.get('direct_velo_points', '').strip()
            present_coureurs = request.form.getlist('present_coureurs')
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
                return render_template('admin/create_questionnaire.html', equipes=equipes, coureurs=coureurs, selected_team_id=team_id)
            questionnaire = Questionnaire(
                course_name=course_name,
                course_date=datetime.strptime(course_date, '%Y-%m-%d').date(),
                direct_velo_points=int(direct_velo_points),
                created_by=current_user.id
            )
            db.session.add(questionnaire)
            db.session.flush()
            for coureur_id in present_coureurs:
                participant = QuestionnaireParticipant(
                    questionnaire_id=questionnaire.id,
                    user_id=int(coureur_id)
                )
                db.session.add(participant)
            db.session.commit()
            
            # Envoyer les notifications WhatsApp aux coureurs
            from app.whatsapp_service import WhatsAppService
            
            whatsapp_service = WhatsAppService()
            whatsapp_sent = 0
            whatsapp_errors = 0
            
            for coureur_id in present_coureurs:
                coureur = User.query.get(int(coureur_id))
                if coureur and coureur.telephone and coureur.notifications_sms:
                    clean_number = whatsapp_service._clean_phone_number(coureur.telephone)
                    date_str = questionnaire.course_date.strftime('%d/%m/%Y')
                    success, message = whatsapp_service.send_questionnaire_template(
                        clean_number,
                        coureur.prenom,
                        questionnaire.course_name,
                        date_str
                    )
                    if success:
                        whatsapp_sent += 1
                    else:
                        whatsapp_errors += 1
                        current_app.logger.warning(f"Erreur WhatsApp pour {coureur.prenom} {coureur.nom}: {message}")
            
            nb_coureurs = len(present_coureurs)
            flash_message = f'Questionnaire créé avec succès pour la course "{course_name}" avec {nb_coureurs} coureurs et {direct_velo_points} points Direct Vélo!'
            
            if whatsapp_sent > 0:
                flash_message += f' {whatsapp_sent} notification(s) WhatsApp envoyée(s).'
            if whatsapp_errors > 0:
                flash_message += f' {whatsapp_errors} erreur(s) WhatsApp.'
                
            flash(flash_message, 'success')
            return redirect(url_for('main.admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur création questionnaire: {e}")
            flash('Erreur lors de la création du questionnaire.', 'danger')
            return render_template('admin/create_questionnaire.html', equipes=equipes, coureurs=coureurs, selected_team_id=team_id)
    return render_template('admin/create_questionnaire.html', equipes=equipes, coureurs=coureurs, selected_team_id=team_id)

def get_coureurs_list():
    """Récupère la liste des coureurs actifs pour l'affichage"""
    user = current_user
    try:
        return User.query.filter_by(role='coureur', is_active=True).order_by(User.nom).all()
    except Exception as e:
        current_app.logger.error(f"Erreur récupération coureurs: {e}")
        return []

@main_bp.route('/coureur/dashboard')
@login_required
def coureur_dashboard():
    user = current_user
    try:
        if not user.is_authenticated:
            return redirect(url_for('main.login'))
        user = User.query.get(current_user.id)
        
        # Calculer le nombre de questionnaires à remplir (en attente)
        user_id = current_user.id
        user_team_id = user.team_id
        nb_questionnaires = QuestionnaireParticipant.query.filter_by(user_id=user_id, has_responded=False).count()
        
        # Calculer le classement du coureur
        classement_mois, classement_annee = calculate_coureur_ranking(user_id)
        
        return render_template('coureur/dashboard.html', 
                             username=current_user.prenom + ' ' + current_user.nom, 
                             current_user=user,
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
    user = current_user
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import func
        
        # Obtenir la date actuelle
        now = get_current_date()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_of_year = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Récupérer tous les coureurs
        all_coureurs = User.query.filter_by(role='coureur', is_active=True, team_id=user.team_id).all()
        
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
                'username': coureur.prenom + ' ' + coureur.nom,
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
    user = current_user
    if 'user_id' not in session:
        return "Non connecté"
    if not user.is_authenticated:
        return "Non connecté"
    user = User.query.get(current_user.id)
    if not user:
        return "Utilisateur non trouvé"
    debug_info = f"""
    <h2>Informations de debug</h2>
    <p><strong>Username:</strong> {user.prenom} {user.nom}</p>
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
    user = current_user
    try:
        if not user.is_authenticated:
            return redirect(url_for('main.login'))
        user = User.query.get(current_user.id)
        if user is None:
            flash('Utilisateur non trouvé.', 'danger')
            return redirect(url_for('main.login'))
        user.role = 'admin'
        user.is_active = True
        db.session.commit()
        session['role'] = 'admin'
        flash(f'Rôle admin forcé pour {user.prenom} {user.nom}', 'success')
        return redirect(url_for('main.debug_user'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur force admin role: {e}")
        flash('Erreur lors de la modification du rôle.', 'danger')
        return redirect(url_for('main.debug_user'))

@main_bp.route('/logout')
def logout():
    user = current_user
    try:
        session.pop('user_id', None)
        session.pop('prenom', None)
        session.pop('nom', None)
        session.pop('role', None)
        flash('Vous avez été déconnecté.', 'info')
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la déconnexion: {e}")
    return redirect(url_for('main.index'))

@main_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    user = current_user
    if request.method == 'POST':
        if not user.is_authenticated:
            return redirect(url_for('main.login'))
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        try:
            user = User.query.get(current_user.id)
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
    user = current_user
    if request.method == 'POST':
        if not user.is_authenticated:
            return redirect(url_for('main.login'))
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
    user = current_user
    try:
        if not user.is_authenticated:
            return redirect(url_for('main.login'))
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
@login_required
def coureur_questionnaires():
    user = current_user
    try:
        if not user.is_authenticated:
            return redirect(url_for('main.login'))
        # Récupérer les questionnaires où le coureur est participant
        user_id = current_user.id
        user_team_id = user.team_id
        participations = QuestionnaireParticipant.query.filter_by(user_id=user_id).all()
        
        questionnaires = []
        for participation in participations:
            questionnaire = participation.questionnaire
            if questionnaire:
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
@login_required
def fill_questionnaire(questionnaire_id):
    user = current_user
    try:
        if not user.is_authenticated:
            return redirect(url_for('main.login'))
        user_id = current_user.id
        
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
                    errors.append(f"Veuillez noter {participant.user.prenom} {participant.user.nom}")
                elif not rating.isdigit() or int(rating) < 1 or int(rating) > 10:
                    errors.append(f"La note pour {participant.user.prenom} {participant.user.nom} doit être entre 1 et 10")
                else:
                    responses[participant.user_id] = int(rating)
            # Récupérer le commentaire général (facultatif)
            comment = request.form.get('comment', '').strip()
            
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
                participation.response_date = get_current_date()
                participation.comment = comment  # Enregistrer le commentaire général
                
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
@login_required
def questionnaire_results(questionnaire_id):
    user = current_user
    try:
        if not user.is_authenticated:
            return redirect(url_for('main.login'))
        user_id = current_user.id
        user_team_id = user.team_id
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
                'evaluated_name': response.evaluated.prenom + ' ' + response.evaluated.nom,
                'rating': response.rating,
                'created_at': response.created_at
            })
        
        return render_template('coureur/questionnaire_results.html', 
                             questionnaire=questionnaire, 
                             results=results,
                             comment=participation.comment)
        
    except Exception as e:
        current_app.logger.error(f"Erreur résultats questionnaire: {e}")
        flash('Erreur lors du chargement des résultats.', 'danger')
        return redirect(url_for('main.coureur_questionnaires'))

@main_bp.route('/coureur/points-details')
@login_required
def coureur_points_details():
    now = get_current_date()
    
    # Calculer le début du mois actuel
    start_of_current_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Sécurisation des conversions en int
    month_raw = request.args.get('month')
    if month_raw is not None and str(month_raw).isdigit():
        selected_month = int(month_raw)
    else:
        selected_month = now.month
        
    year_raw = request.args.get('year')
    if year_raw is not None and str(year_raw).isdigit():
        selected_year = int(year_raw)
    else:
        selected_year = now.year
    
    # Redirection si la date sélectionnée est dans le futur
    if selected_year > now.year or (selected_year == now.year and selected_month > now.month):
        return redirect(url_for('main.coureur_points_details', month=now.month, year=now.year))
        
    current_month_name = month_names[now.month - 1]
    selected_month_name = month_names[selected_month - 1]
    """
    Affiche les détails des points gagnés par course pour le coureur
    """
    user = current_user
    try:
        if not user.is_authenticated:
            return redirect(url_for('main.login'))
        user_id = current_user.id
        user_team_id = user.team_id
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
        
        # Calculer d'abord les moyennes globales (toutes les courses)
        for participation, questionnaire in participations:
            # Calculer la note moyenne personnelle reçue pour cette course
            note_moyenne_perso = db.session.query(func.avg(QuestionnaireResponse.rating)).filter(
                QuestionnaireResponse.questionnaire_id == questionnaire.id,
                QuestionnaireResponse.evaluated_id == user_id
            ).scalar() or 0
            
            # Accumuler pour le calcul de la moyenne globale
            if float(note_moyenne_perso) > 0:
                total_note_moyenne += float(note_moyenne_perso)
                nb_courses_avec_notes += 1
                
                # Accumuler pour le calcul de la moyenne du mois actuel
                if questionnaire.course_date >= start_of_current_month.date():
                    total_note_moyenne_mois += float(note_moyenne_perso)
                    nb_courses_avec_notes_mois += 1
        
        # Maintenant filtrer et afficher seulement les courses du mois sélectionné
        for participation, questionnaire in participations:
            # Filtrer par mois sélectionné
            if (questionnaire.course_date.year == selected_year and 
                questionnaire.course_date.month == selected_month):
                
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
                
                # Calculer la note maximale et minimale personnelles reçues pour cette course
                note_max_perso = db.session.query(func.max(QuestionnaireResponse.rating)).filter(
                    QuestionnaireResponse.questionnaire_id == questionnaire.id,
                    QuestionnaireResponse.evaluated_id == user_id
                ).scalar() or 0
                
                note_min_perso = db.session.query(func.min(QuestionnaireResponse.rating)).filter(
                    QuestionnaireResponse.questionnaire_id == questionnaire.id,
                    QuestionnaireResponse.evaluated_id == user_id
                ).scalar() or 0
                
                # Récupérer les IDs des membres de l'équipe
                equipe_user_ids = [u.id for u in User.query.filter_by(team_id=user_team_id).all()]
                # Calculer la note moyenne équipe pour cette course (moyenne des notes reçues par les membres de l'équipe)
                note_moyenne_equipe = db.session.query(func.avg(QuestionnaireResponse.rating)).filter(
                    QuestionnaireResponse.questionnaire_id == questionnaire.id,
                    QuestionnaireResponse.evaluated_id.in_(equipe_user_ids)
                ).scalar() or 0
                
                # Calculer le nombre de votants pour cette course
                nb_votants = db.session.query(QuestionnaireResponse.evaluator_id).filter(
                    QuestionnaireResponse.questionnaire_id == questionnaire.id
                ).distinct().count()
                
                # Accumuler pour le calcul de la moyenne du mois sélectionné
                if float(note_moyenne_perso) > 0:
                    total_note_moyenne_selected_month += float(note_moyenne_perso)
                    nb_courses_avec_notes_selected_month += 1
                
                courses_details.append({
                    'course_name': questionnaire.course_name,
                    'course_date': questionnaire.course_date,
                    'direct_velo_points': questionnaire.direct_velo_points,
                    'note_moyenne_perso': round(float(note_moyenne_perso), 1),
                    'note_max_perso': int(note_max_perso) if note_max_perso else 0,
                    'note_min_perso': int(note_min_perso) if note_min_perso else 0,
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
@login_required
def admin_questionnaires():
    user = current_user
    try:
        if not user.is_authenticated:
            return redirect(url_for('main.login'))
        
        from datetime import datetime
        now = get_current_date()
        
        # Récupération des paramètres de filtrage
        team_id = request.args.get('team_id', type=int)
        season_raw = request.args.get('season')
        month_raw = request.args.get('month')
        year_raw = request.args.get('year')
        
        # Traitement des paramètres de saison
        if season_raw is not None and str(season_raw).isdigit():
            selected_season = int(season_raw)
        else:
            # Calcul de la saison courante selon la logique du site
            if now.month >= 11:
                selected_season = now.year + 1
            else:
                selected_season = now.year

        # Traitement des paramètres de mois
        if month_raw is not None and str(month_raw).isdigit():
            selected_month = int(month_raw)
        else:
            selected_month = now.month
            
        if year_raw is not None and str(year_raw).isdigit():
            selected_year = int(year_raw)
        else:
            selected_year = now.year
        
        # Validation des paramètres de date
        if selected_year > 2030 or selected_month > 12 or selected_month < 1:
            selected_month = now.month
            selected_year = now.year
        
        # Construction de la requête de base
        query = Questionnaire.query
        
        # Filtrage par équipe
        if team_id:
            query = (query
                .join(QuestionnaireParticipant, Questionnaire.id == QuestionnaireParticipant.questionnaire_id)
                .join(User, QuestionnaireParticipant.user_id == User.id)
                .filter(User.team_id == team_id)
                .distinct())
        
        # Filtrage par saison
        if selected_season:
            season_start = datetime(selected_season - 1, 11, 1).date()
            season_end = datetime(selected_season, 10, 31).date()
            query = query.filter(
                Questionnaire.course_date >= season_start,
                Questionnaire.course_date <= season_end
            )
        
        # Filtrage par mois spécifique
        if selected_month and selected_year:
            month_start = datetime(selected_year, selected_month, 1).date()
            if selected_month < 12:
                month_end = datetime(selected_year, selected_month + 1, 1).date()
            else:
                month_end = datetime(selected_year + 1, 1, 1).date()
            query = query.filter(
                Questionnaire.course_date >= month_start,
                Questionnaire.course_date < month_end
            )
        
        questionnaires = query.order_by(Questionnaire.course_date.desc()).all()
        
        # Récupération des équipes
        teams = Team.query.filter_by(actif=True).all()
        
        # Génération des options de saison
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
        
        season_options = []
        for s in sorted(available_seasons, reverse=True):
            season_options.append({'year': s, 'selected': s == selected_season})
        
        # Génération des options de mois pour la saison sélectionnée
        month_options = []
        season_start_year = selected_season - 1
        current_year = now.year
        current_month = now.month
        for year in [season_start_year, selected_season]:
            start_month = 11 if year == season_start_year else 1
            end_month = 12 if year == season_start_year else 10
            for month in range(start_month, end_month + 1):
                if (selected_season == (current_year if current_month < 11 else current_year+1)) and (year == current_year and month > current_month):
                    continue
                month_options.append({
                    'year': year,
                    'month': month,
                    'selected': year == selected_year and month == selected_month
                })
        
        # Calcul des statistiques pour chaque questionnaire
        participants_map = {}
        for q in questionnaires:
            participants = db.session.query(User.prenom, User.nom, QuestionnaireParticipant.has_responded).join(QuestionnaireParticipant, User.id == QuestionnaireParticipant.user_id).filter(QuestionnaireParticipant.questionnaire_id == q.id).all()
            participants_map[q.id] = [{'prenom': p[0], 'nom': p[1], 'has_responded': p[2]} for p in participants]
        
        return render_template('admin/questionnaires.html', 
                             questionnaires=questionnaires, 
                             teams=teams, 
                             participants_map=participants_map, 
                             selected_team_id=team_id,
                             season_options=season_options,
                             month_options=month_options,
                             selected_season=selected_season,
                             selected_month=selected_month,
                             selected_year=selected_year)
    except Exception as e:
        current_app.logger.error(f"Erreur liste questionnaires: {e}")
        flash('Erreur lors du chargement des questionnaires.', 'danger')
        return redirect(url_for('main.admin_dashboard'))

@main_bp.route('/admin/questionnaire/<int:questionnaire_id>/results')
@login_required
def admin_questionnaire_results(questionnaire_id):
    """
    Affiche les résultats détaillés d'un questionnaire pour l'admin
    """
    user = current_user
    try:
        if not user.is_authenticated:
            return redirect(url_for('main.login'))
        # Récupérer le questionnaire
        questionnaire = Questionnaire.query.get_or_404(questionnaire_id)
        
        # Récupérer tous les participants avec leurs IDs
        participants = db.session.query(
            User.id,
            User.prenom,
            User.nom,
            QuestionnaireParticipant.has_responded,
            QuestionnaireParticipant.response_date,
            QuestionnaireParticipant.comment
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
            User.prenom.label('evaluator_prenom'),
            User.nom.label('evaluator_nom')
        ).join(
            User, QuestionnaireResponse.evaluator_id == User.id
        ).filter(
            QuestionnaireResponse.questionnaire_id == questionnaire_id
        ).all()
        
        # Récupérer les informations des utilisateurs évalués
        evaluated_users = {}
        for response in all_responses:
            if response.evaluated_id not in evaluated_users:
                evaluated_user = User.query.get(response.evaluated_id)
                if evaluated_user:
                    evaluated_users[response.evaluated_id] = {
                        'prenom': evaluated_user.prenom,
                        'nom': evaluated_user.nom
                    }
        
        # Organiser les données pour l'affichage
        results_data = []
        for participant in participants:
            user_id = participant.id
            prenom = participant.prenom
            nom = participant.nom
            
            # Récupérer les notes données par ce participant
            participant_responses = []
            for response in all_responses:
                if response.evaluator_id == user_id:
                    evaluated_user_info = evaluated_users.get(response.evaluated_id, {})
                    evaluated_name = f"{evaluated_user_info.get('prenom', '')} {evaluated_user_info.get('nom', '')}".strip()
                    participant_responses.append({
                        'evaluated_name': evaluated_name,
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
                'prenom': prenom,
                'nom': nom,
                'has_responded': participant.has_responded,
                'response_date': participant.response_date,
                'responses_given': participant_responses,
                'avg_rating_received': round(avg_rating_received, 1),
                'nb_ratings_received': len(received_ratings),
                'comment': participant.comment
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
    user = current_user
    try:
        if not user.is_authenticated:
            return redirect(url_for('main.login'))
        user_id = current_user.id
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
        <h2>Debug Classement - {user.prenom} {user.nom}</h2>
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
@login_required
def coureur_rankings():
    """
    Affiche les classements du mois et de l'année
    """
    user = current_user
    try:
        if not user.is_authenticated:
            return redirect(url_for('main.login'))
        from datetime import datetime
        from sqlalchemy import func
        
        # Obtenir la date actuelle et le mois sélectionné
        now = get_current_date()
        
        # Sécurisation des conversions en int
        month_raw = request.args.get('month')
        if month_raw is not None and str(month_raw).isdigit():
            selected_month = int(month_raw)
        else:
            selected_month = now.month
            
        year_raw = request.args.get('year')
        if year_raw is not None and str(year_raw).isdigit():
            selected_year = int(year_raw)
        else:
            selected_year = now.year
        
        # Redirection si la date sélectionnée est dans le futur
        if selected_year > now.year or (selected_year == now.year and selected_month > now.month):
            return redirect(url_for('main.coureur_rankings', month=now.month, year=now.year))
        
        # Calculer la date de début du mois sélectionné
        start_of_selected_month = datetime(selected_year, selected_month, 1)
        start_of_current_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_of_year = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Récupérer tous les coureurs
        all_coureurs = User.query.filter_by(role='coureur', is_active=True, team_id=user.team_id).all()
        
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
                'username': coureur.prenom + ' ' + coureur.nom,
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
@login_required
def admin_course_statistics():
    """
    Affiche les statistiques des courses avec les notes moyennes et points de chaque coureur, filtrables par équipe
    """
    user = current_user
    try:
        if not user.is_authenticated:
            return redirect(url_for('main.login'))
        from sqlalchemy import func
        from datetime import datetime
        now = get_current_date()
        
        # Sécurisation des conversions en int
        month_raw = request.args.get('month')
        if month_raw is not None and str(month_raw).isdigit():
            selected_month = int(month_raw)
        else:
            selected_month = now.month
            
        year_raw = request.args.get('year')
        if year_raw is not None and str(year_raw).isdigit():
            selected_year = int(year_raw)
        else:
            selected_year = now.year
            
        season_raw = request.args.get('season')
        if season_raw is not None and str(season_raw).isdigit():
            selected_season = int(season_raw)
        else:
            selected_season = now.year
            
        team_id_raw = request.args.get('team_id')
        if team_id_raw is not None and str(team_id_raw).isdigit():
            selected_team_id = int(team_id_raw)
        else:
            selected_team_id = None
        
        # Redirection si la date sélectionnée est dans le futur
        if selected_year > now.year or (selected_year == now.year and selected_month > now.month):
            return redirect(url_for('main.admin_course_statistics', month=now.month, year=now.year, season=selected_season, team_id=selected_team_id))
        
        # Validation supplémentaire pour éviter les erreurs SQL
        if selected_year > 2030 or selected_month > 12 or selected_month < 1:
            return redirect(url_for('main.admin_course_statistics', month=now.month, year=now.year, season=selected_season, team_id=selected_team_id))
        
        # Récupérer la liste des équipes actives
        teams = Team.query.filter_by(actif=True).order_by(Team.nom).all()
        
        # Créer les dates de début et fin du mois de manière sécurisée
        month_start_date = datetime(selected_year, selected_month, 1).date()
        if selected_month < 12:
            month_end_date = datetime(selected_year, selected_month + 1, 1).date()
        else:
            month_end_date = datetime(selected_year + 1, 1, 1).date()
        
        # Récupérer les questionnaires du mois sélectionné
        questionnaires = Questionnaire.query.filter(
            Questionnaire.course_date >= month_start_date,
            Questionnaire.course_date < month_end_date
        ).order_by(Questionnaire.course_date.desc()).all()
        course_stats = []
        for questionnaire in questionnaires:
            # Récupérer tous les participants de ce questionnaire
            participants_query = db.session.query(
                User.id,
                User.prenom,
                User.nom,
                QuestionnaireParticipant.has_responded,
                User.team_id
            ).join(
                QuestionnaireParticipant, User.id == QuestionnaireParticipant.user_id
            ).filter(
                QuestionnaireParticipant.questionnaire_id == questionnaire.id
            )
            if selected_team_id:
                participants_query = participants_query.filter(User.team_id == selected_team_id)
            participants = participants_query.all()
            participant_stats = []
            all_ratings = []
            for participant in participants:
                user_id = participant.id
                prenom = participant.prenom
                nom = participant.nom
                # Récupérer les notes reçues par ce participant
                received_ratings = db.session.query(QuestionnaireResponse.rating).filter(
                    QuestionnaireResponse.questionnaire_id == questionnaire.id,
                    QuestionnaireResponse.evaluated_id == user_id
                ).all()
                avg_rating = 0
                min_rating = None
                max_rating = None
                if received_ratings:
                    ratings = [r.rating for r in received_ratings]
                    avg_rating = sum(ratings) / len(ratings)
                    min_rating = min(ratings)
                    max_rating = max(ratings)
                    all_ratings.extend(ratings)
                points = avg_rating * questionnaire.direct_velo_points
                participant_stats.append({
                    'username': prenom + ' ' + nom,
                    'avg_rating': round(avg_rating, 1),
                    'min_rating': min_rating,
                    'max_rating': max_rating,
                    'points': round(points, 1)
                })
            team_avg_rating = 0
            if all_ratings:
                team_avg_rating = sum(all_ratings) / len(all_ratings)
            if participant_stats:  # N'ajouter la course que s'il y a des participants après filtrage
                course_stats.append({
                    'questionnaire': questionnaire,
                    'participants': participant_stats,
                    'team_avg_rating': round(team_avg_rating, 1),
                    'nb_participants': len(participants)
                })
        # ... (reste inchangé)
        # Saisons, mois, etc.
        # ...
        # Générer la liste des saisons pour la dropdown (après avoir déterminé la saison sélectionnée)
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
        season = int(selected_season)
        season_options = []
        for s in sorted(available_seasons, reverse=True):
            season_options.append({'year': s, 'selected': s == season})
        # Générer les options de mois pour la saison sélectionnée
        month_options = []
        season_start_year = season - 1
        current_year = now.year
        current_month = now.month
        for year in [season_start_year, season]:
            start_month = 11 if year == season_start_year else 1
            end_month = 12 if year == season_start_year else 10
            for month in range(start_month, end_month + 1):
                if (season == (current_year if current_month < 11 else current_year+1)) and (year == current_year and month > current_month):
                    continue
                month_options.append({
                    'year': year,
                    'month': month,
                    'selected': year == selected_year and month == selected_month
                })
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
                             selected_season=selected_season,
                             teams=teams,
                             selected_team_id=selected_team_id)
    except Exception as e:
        current_app.logger.error(f"Erreur statistiques courses admin: {e}")
        flash('Erreur lors du chargement des statistiques.', 'danger')
        return redirect(url_for('main.admin_dashboard'))

@main_bp.route('/admin/global-rankings')
@login_required
def admin_global_rankings():
    """
    Affiche le classement global de la saison en cours, du mois en cours et des mois précédents (sélection via liste déroulante)
    """
    user = current_user
    try:
        if not user.is_authenticated:
            return redirect(url_for('main.login'))
        team_id_raw = request.args.get('team_id')
        if team_id_raw is not None and str(team_id_raw).isdigit():
            team_id = int(team_id_raw)
        else:
            team_id = None
        from datetime import datetime
        from sqlalchemy import func
        now = get_current_date()
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
        selected_season = request.args.get('season')
        if selected_season is not None and str(selected_season).isdigit():
            season = int(selected_season)
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
        month_raw = request.args.get('month')
        if month_raw is not None and str(month_raw).isdigit():
            selected_month = int(month_raw)
        else:
            selected_month = now.month
            
        year_raw = request.args.get('year')
        if year_raw is not None and str(year_raw).isdigit():
            selected_year = int(year_raw)
        else:
            selected_year = now.year
        
        # Redirection si la date sélectionnée est dans le futur
        if selected_year > now.year or (selected_year == now.year and selected_month > now.month):
            return redirect(url_for('main.admin_global_rankings', month=now.month, year=now.year, season=season, team_id=team_id))
        
        # Validation supplémentaire pour éviter les erreurs SQL
        if selected_year > 2030 or selected_month > 12 or selected_month < 1:
            return redirect(url_for('main.admin_global_rankings', month=now.month, year=now.year, season=season, team_id=team_id))
        
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
            if total_points > 0:  # Ne pas afficher les coureurs avec 0 points
                saison_points.append({'prenom': coureur.prenom, 'nom': coureur.nom, 'points': round(total_points, 1), 'team_id': coureur.team_id})
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
            if total_points > 0:  # Ne pas afficher les coureurs avec 0 points
                mois_points.append({'prenom': coureur.prenom, 'nom': coureur.nom, 'points': round(total_points, 1), 'team_id': coureur.team_id})
        mois_points.sort(key=lambda x: x['points'], reverse=True)
        
        # Classement des notes moyennes de la saison
        saison_notes = []
        for coureur in coureurs:
            participations = db.session.query(QuestionnaireParticipant, Questionnaire).join(
                Questionnaire, QuestionnaireParticipant.questionnaire_id == Questionnaire.id
            ).filter(
                QuestionnaireParticipant.user_id == coureur.id,
                Questionnaire.course_date >= season_start.date(),
                Questionnaire.course_date <= season_end.date()
            ).all()
            total_rating = 0
            nb_courses_avec_notes = 0
            for participation, questionnaire in participations:
                avg_rating = db.session.query(func.avg(QuestionnaireResponse.rating)).filter(
                    QuestionnaireResponse.questionnaire_id == questionnaire.id,
                    QuestionnaireResponse.evaluated_id == coureur.id
                ).scalar() or 0
                if float(avg_rating) > 0:
                    total_rating += float(avg_rating)
                    nb_courses_avec_notes += 1
            if nb_courses_avec_notes > 0:
                avg_rating_season = round(total_rating / nb_courses_avec_notes, 1)
                saison_notes.append({'prenom': coureur.prenom, 'nom': coureur.nom, 'note': avg_rating_season, 'team_id': coureur.team_id})
        saison_notes.sort(key=lambda x: x['note'], reverse=True)
        
        # Classement des notes moyennes du mois sélectionné
        mois_notes = []
        for coureur in coureurs:
            participations = db.session.query(QuestionnaireParticipant, Questionnaire).join(
                Questionnaire, QuestionnaireParticipant.questionnaire_id == Questionnaire.id
            ).filter(
                QuestionnaireParticipant.user_id == coureur.id,
                Questionnaire.course_date >= month_start.date(),
                Questionnaire.course_date < month_end.date()
            ).all()
            total_rating = 0
            nb_courses_avec_notes = 0
            for participation, questionnaire in participations:
                avg_rating = db.session.query(func.avg(QuestionnaireResponse.rating)).filter(
                    QuestionnaireResponse.questionnaire_id == questionnaire.id,
                    QuestionnaireResponse.evaluated_id == coureur.id
                ).scalar() or 0
                if float(avg_rating) > 0:
                    total_rating += float(avg_rating)
                    nb_courses_avec_notes += 1
            if nb_courses_avec_notes > 0:
                avg_rating_month = round(total_rating / nb_courses_avec_notes, 1)
                mois_notes.append({'prenom': coureur.prenom, 'nom': coureur.nom, 'note': avg_rating_month, 'team_id': coureur.team_id})
        mois_notes.sort(key=lambda x: x['note'], reverse=True)
        # Pour affichage du mois
        month_names = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
        selected_month_name = month_names[selected_month-1]
        # Générer la liste des saisons pour la dropdown (après avoir déterminé la saison sélectionnée)
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
        # Utiliser la variable season déjà calculée et sécurisée
        season_options = []
        for s in sorted(available_seasons, reverse=True):
            season_options.append({'year': s, 'selected': s == season})
        # Générer les options de mois pour la saison sélectionnée
        month_options = []
        season_start_year = season - 1
        current_year = now.year
        current_month = now.month
        for year in [season_start_year, season]:
            start_month = 11 if year == season_start_year else 1
            end_month = 12 if year == season_start_year else 10
            for month in range(start_month, end_month + 1):
                if (season == (current_year if current_month < 11 else current_year+1)) and (year == current_year and month > current_month):
                    continue
                month_options.append({
                    'year': year,
                    'month': month,
                    'selected': year == selected_year and month == selected_month
                })
        month_names = [
            "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
            "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
        ]
        selected_month_name = month_names[selected_month - 1]
        if team_id:
            # Filtrer les classements pour ne prendre que les membres de l'équipe sélectionnée
            saison_points = [c for c in saison_points if c['team_id'] == team_id]
            mois_points = [c for c in mois_points if c['team_id'] == team_id]
            saison_notes = [c for c in saison_notes if c['team_id'] == team_id]
            mois_notes = [c for c in mois_notes if c['team_id'] == team_id]
        teams = Team.query.filter_by(actif=True).all()
        return render_template('admin/global_rankings.html',
            saison_points=saison_points,
            mois_points=mois_points,
            saison_notes=saison_notes,
            mois_notes=mois_notes,
            season=season,
            season_options=season_options,
            months=months,
            selected_month=selected_month,
            selected_year=selected_year,
            selected_month_name=selected_month_name,
            teams=teams,
            int=int  # Ajout pour Jinja
        )
    except Exception as e:
        current_app.logger.error(f"Erreur classements globaux: {e}")
        flash('Erreur lors du chargement des classements globaux.', 'danger')
        return redirect(url_for('main.admin_dashboard'))

@main_bp.route('/admin/questionnaire/<int:questionnaire_id>/delete', methods=['POST'])
@login_required
def delete_questionnaire(questionnaire_id):
    """
    Permet à l'admin de supprimer un questionnaire et toutes ses données associées
    """
    user = current_user
    try:
        if not user.is_authenticated:
            return redirect(url_for('main.login'))
        questionnaire = Questionnaire.query.get_or_404(questionnaire_id)
        db.session.delete(questionnaire)
        db.session.commit()
        flash('Le questionnaire a bien été supprimé.', 'success')
        return redirect(url_for('main.admin_questionnaires'))
    except Exception as e:
        current_app.logger.error(f"Erreur suppression questionnaire: {e}")
        flash("Erreur lors de la suppression du questionnaire.", 'danger')
        return redirect(url_for('main.admin_questionnaire_results', questionnaire_id=questionnaire_id))

@main_bp.route('/test-protected')
@login_required
def test_protected():
    return f"Connecté en tant que : {current_user.prenom} ({current_user.role})"

@main_bp.route('/admin/create-team', methods=['POST'])
@login_required
def create_team():
    user = current_user
    if not user.is_admin():
        flash('Accès interdit. Privilèges administrateur requis.', 'danger')
        return redirect(url_for('main.admin_dashboard'))
    nom = request.form.get('nom', '').strip()
    description = request.form.get('description', '').strip()
    couleur = request.form.get('couleur', '').strip() or None
    coureurs_ids = request.form.getlist('coureurs')
    if not nom:
        flash("Le nom de l'équipe est requis.", 'danger')
        return redirect(url_for('main.admin_dashboard'))
    # Vérifier unicité du nom
    if Team.query.filter_by(nom=nom).first():
        flash("Une équipe avec ce nom existe déjà.", 'danger')
        return redirect(url_for('main.admin_dashboard'))
    try:
        team = Team(nom=nom, description=description, couleur=couleur, actif=True)
        db.session.add(team)
        db.session.commit()
        # Affecter les coureurs sélectionnés à l'équipe
        if coureurs_ids:
            for coureur_id in coureurs_ids:
                if coureur_id is not None and str(coureur_id).isdigit():
                    coureur = User.query.get(int(coureur_id))
                    if coureur and coureur.role == 'coureur':
                        coureur.team_id = team.id
            db.session.commit()
        flash(f"Équipe '{nom}' créée avec succès !", 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur création équipe : {e}")
        flash("Erreur lors de la création de l'équipe.", 'danger')
    return redirect(url_for('main.admin_dashboard'))

@main_bp.route('/admin/teams')
@login_required
def admin_teams():
    user = current_user
    if not user.is_admin():
        flash('Accès interdit. Privilèges administrateur requis.', 'danger')
        return redirect(url_for('main.admin_dashboard'))
    teams = Team.query.order_by(Team.nom).all()
    coureurs_sans_equipe = User.query.filter_by(role='coureur', is_active=True, team_id=None).order_by(User.nom, User.prenom).all()
    return render_template('admin/teams.html', teams=teams, coureurs_sans_equipe=coureurs_sans_equipe)

@main_bp.route('/admin/teams/<int:team_id>/delete', methods=['POST'])
@login_required
def delete_team(team_id):
    user = current_user
    if not user.is_admin():
        flash('Accès interdit. Privilèges administrateur requis.', 'danger')
        return redirect(url_for('main.admin_teams'))
    team = Team.query.get_or_404(team_id)
    try:
        db.session.delete(team)
        db.session.commit()
        flash(f"Équipe '{team.nom}' supprimée avec succès.", 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur suppression équipe : {e}")
        flash("Erreur lors de la suppression de l'équipe.", 'danger')
    return redirect(url_for('main.admin_teams'))

@main_bp.route('/admin/teams/<int:team_id>/affecter', methods=['POST'])
@login_required
def affecter_coureurs(team_id):
    if not current_user.is_admin():
        flash("Accès interdit.", "danger")
        return redirect(url_for('main.admin_teams'))
    team = Team.query.get_or_404(team_id)
    coureur_ids = request.form.getlist('coureur_ids')
    if not coureur_ids:
        flash("Aucun coureur sélectionné.", "warning")
        return redirect(url_for('main.admin_teams'))
    coureurs = User.query.filter(User.id.in_(coureur_ids), User.team_id==None).all()
    for coureur in coureurs:
        coureur.team_id = team.id
    db.session.commit()
    flash(f"{len(coureurs)} coureur(s) affecté(s) à l'équipe {team.nom}.", "success")
    return redirect(url_for('main.admin_teams')) 

@main_bp.route('/admin/teams/<int:team_id>/retirer/<int:coureur_id>', methods=['POST'])
@login_required
def retirer_coureur(team_id, coureur_id):
    if not current_user.is_admin():
        flash("Accès interdit.", "danger")
        return redirect(url_for('main.admin_teams'))
    team = Team.query.get_or_404(team_id)
    coureur = User.query.get_or_404(coureur_id)
    if coureur.team_id != team.id:
        flash("Ce coureur n'appartient pas à cette équipe.", "warning")
        return redirect(url_for('main.admin_teams'))
    coureur.team_id = None
    db.session.commit()
    flash(f"{coureur.prenom} {coureur.nom} retiré de l'équipe {team.nom}.", "success")
    return redirect(url_for('main.admin_teams'))

@main_bp.route('/admin/api/coureurs_par_equipe/<int:team_id>')
@login_required
def api_coureurs_par_equipe(team_id):
    coureurs = User.query.filter_by(role='coureur', is_active=True, team_id=team_id).order_by(User.nom).all()
    data = [
        {
            'id': c.id,
            'prenom': c.prenom,
            'nom': c.nom,
            'email': c.email
        } for c in coureurs
    ]
    return jsonify(data)

@main_bp.route('/profile')
@login_required
def profile():
    """Affiche la page de profil utilisateur"""
    user = current_user
    from app.models import Team
    teams = Team.query.filter_by(actif=True).order_by(Team.nom).all()
    return render_template('coureur/profile.html', current_user=user, teams=teams)

@main_bp.route('/edit-profile', methods=['POST'])
@login_required
def edit_profile():
    """Modifie le profil utilisateur"""
    user = current_user
    try:
        # Récupération des données du formulaire
        prenom = request.form['prenom'].strip()
        nom = request.form['nom'].strip()
        email = request.form['email'].strip().lower()
        telephone = request.form.get('telephone', '').strip()
        notifications_sms = request.form.get('notifications_sms') == 'on'
        team_id = request.form.get('team_id')
        
        # Validation des données
        errors = []
        if not telephone:
            errors.append("Le numéro de téléphone est obligatoire.")
        
        is_valid_prenom, prenom_msg = User.validate_prenom(prenom)
        if not is_valid_prenom:
            errors.append(prenom_msg)
        
        is_valid_nom, nom_msg = User.validate_nom(nom)
        if not is_valid_nom:
            errors.append(nom_msg)
        
        if not User.validate_email(email):
            errors.append("Format d'email invalide")
        
        is_valid_telephone, telephone_msg = User.validate_telephone(telephone)
        if not is_valid_telephone:
            errors.append(telephone_msg)
        
        # Vérifier si l'email est déjà utilisé par un autre utilisateur
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != user.id:
            errors.append('Email déjà utilisé par un autre utilisateur')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            from app.models import Team
            teams = Team.query.filter_by(actif=True).order_by(Team.nom).all()
            return render_template('coureur/profile.html', current_user=user, teams=teams)
        
        # Mise à jour du profil
        user.prenom = prenom
        user.nom = nom
        user.email = email
        user.telephone = telephone
        user.notifications_sms = True
        user.team_id = team_id if team_id else None
        
        db.session.commit()
        flash('Profil mis à jour avec succès !', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur modification profil: {e}")
        flash('Erreur lors de la modification du profil.', 'danger')
    
    return redirect(url_for('main.profile'))