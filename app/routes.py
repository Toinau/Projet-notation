from flask import Blueprint, render_template, redirect, url_for, request, flash, session, abort, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User
from app.decorators import login_required, admin_required, coureur_required
from app import db, mail, serializer
from flask_mail import Message
from itsdangerous import SignatureExpired, BadSignature
from datetime import datetime

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

@main_bp.route('/coureur/dashboard')
@coureur_required
def coureur_dashboard():
    try:
        current_user = User.query.get(session['user_id'])
        return render_template('coureur/dashboard.html', username=session['username'], current_user=current_user)
    except Exception as e:
        current_app.logger.error(f"Erreur dashboard coureur: {e}")
        flash('Erreur lors du chargement du dashboard.', 'danger')
        return redirect(url_for('main.dashboard'))

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