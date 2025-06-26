import os
from flask import Flask, render_template, redirect, url_for, request, flash, session, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from functools import wraps
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config.from_object('config.Config')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Configuration email - compatible local ET production
if not app.config.get('MAIL_SERVER'):
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER') or 'antoine.piedagnel@gmail.com'

mail = Mail(app)
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

app.permanent_session_lifetime = timedelta(minutes=30)

# Modèle User amélioré
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='coureur')
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<User {self.username} - {self.role}>'

    def is_admin(self):
        return self.role == 'admin'

    def is_coureur(self):
        return self.role == 'coureur'

# Décorateurs pour la gestion des permissions
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
            return redirect(url_for('login'))
        
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin():
            flash('Accès interdit. Privilèges administrateur requis.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def coureur_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
            return redirect(url_for('login'))
        
        user = User.query.get(session['user_id'])
        if not user or not user.is_coureur():
            flash('Accès réservé aux coureurs.', 'warning')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'coureur')  # Par défaut coureur
        
        # Validation du rôle
        if role not in ['coureur', 'admin']:
            role = 'coureur'
        
        # Vérifier si l'utilisateur existe déjà
        user_exists = User.query.filter_by(username=username).first()
        email_exists = User.query.filter_by(email=email).first()
        
        if user_exists:
            flash('Nom d\'utilisateur déjà utilisé', 'danger')
            return redirect(url_for('register'))
        
        if email_exists:
            flash('Email déjà utilisé', 'danger')
            return redirect(url_for('register'))
        
        # Créer un nouvel utilisateur
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, email=email, password=hashed_password, role=role)
        
        # Ajouter l'utilisateur à la base de données
        db.session.add(new_user)
        db.session.commit()
        
        flash(f'Votre compte {role} a été créé avec succès!', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(username=username).first()
        
        # Vérifier si l'utilisateur existe et si le mot de passe est correct
        if not user or not check_password_hash(user.password, password):
            flash('Veuillez vérifier vos identifiants et réessayer.', 'danger')
            return redirect(url_for('login'))
        
        # Vérifier si le compte est actif
        if not user.is_active:
            flash('Votre compte a été désactivé. Contactez l\'administrateur.', 'danger')
            return redirect(url_for('login'))
        
        # Si les identifiants sont valides, créer une session pour l'utilisateur
        session.permanent = remember
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        
        # Debug - Afficher le rôle dans les logs/console
        print(f"Utilisateur connecté: {user.username}, Rôle: {user.role}, is_admin(): {user.is_admin()}")
        
        flash(f'Bienvenue, {user.username} ({user.role})!', 'success')
        
        # Redirection selon le rôle avec vérification explicite
        if user.role == 'admin':
            print("Redirection vers admin_dashboard")
            return redirect(url_for('admin_dashboard'))
        else:
            print("Redirection vers coureur_dashboard")
            return redirect(url_for('coureur_dashboard'))
    
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    user = User.query.get(session['user_id'])
    print(f"Dashboard - Utilisateur: {user.username}, Rôle: {user.role}, is_admin(): {user.is_admin()}")
    
    if user.role == 'admin':
        print("Redirection dashboard -> admin_dashboard")
        return redirect(url_for('admin_dashboard'))
    else:
        print("Redirection dashboard -> coureur_dashboard")
        return redirect(url_for('coureur_dashboard'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    # Récupérer l'utilisateur actuel pour l'afficher dans le dashboard
    current_user = User.query.get(session['user_id'])
    
    # Statistiques pour l'admin
    total_users = User.query.count()
    total_coureurs = User.query.filter_by(role='coureur').count()
    total_admins = User.query.filter_by(role='admin').count()
    active_users = User.query.filter_by(is_active=True).count()
    inactive_users = User.query.filter_by(is_active=False).count()
    
    # Récupérer tous les utilisateurs pour l'affichage
    all_users = User.query.order_by(User.created_at.desc()).all()
    
    stats = {
        'total_users': total_users,
        'total_coureurs': total_coureurs,
        'total_admins': total_admins,
        'active_users': active_users,
        'inactive_users': inactive_users
    }
    
    return render_template('admin/dashboard.html', 
                         username=session['username'],
                         current_user=current_user,
                         all_users=all_users,
                         stats=stats)

@app.route('/coureur/dashboard')
@coureur_required
def coureur_dashboard():
    current_user = User.query.get(session['user_id'])
    return render_template('coureur/dashboard.html', 
                         username=session['username'],
                         current_user=current_user)

@app.route('/admin/users')
@admin_required
def admin_users():
    # Récupérer tous les utilisateurs triés par date de création (le plus récent en premier)
    users = User.query.order_by(User.created_at.desc()).all()
    current_user_id = session['user_id']
    
    return render_template('admin/users.html', 
                         users=users, 
                         current_user_id=current_user_id)

@app.route('/admin/users/<int:user_id>/toggle', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    
    # Empêcher l'admin de se désactiver lui-même
    if user.id == session['user_id']:
        flash('Vous ne pouvez pas désactiver votre propre compte.', 'warning')
        return redirect(url_for('admin_users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activé' if user.is_active else 'désactivé'
    flash(f'Le compte de {user.username} a été {status}.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Empêcher l'admin de supprimer son propre compte
    if user.id == session['user_id']:
        flash('Vous ne pouvez pas supprimer votre propre compte.', 'warning')
        return redirect(url_for('admin_users'))
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    flash(f'Le compte de {username} a été supprimé.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:user_id>/promote', methods=['POST'])
@admin_required
def promote_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.role == 'coureur':
        user.role = 'admin'
        db.session.commit()
        flash(f'{user.username} a été promu administrateur.', 'success')
    else:
        flash(f'{user.username} est déjà administrateur.', 'info')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:user_id>/demote', methods=['POST'])
@admin_required
def demote_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Empêcher l'admin de se rétrograder lui-même
    if user.id == session['user_id']:
        flash('Vous ne pouvez pas modifier votre propre rôle.', 'warning')
        return redirect(url_for('admin_users'))
    
    if user.role == 'admin':
        user.role = 'coureur'
        db.session.commit()
        flash(f'{user.username} a été rétrogradé en coureur.', 'success')
    else:
        flash(f'{user.username} est déjà coureur.', 'info')
    
    return redirect(url_for('admin_users'))

@app.route('/debug-user')
def debug_user():
    """Route temporaire pour diagnostiquer le problème admin"""
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

@app.route('/force-admin-role')
@login_required
def force_admin_role():
    """Route temporaire pour forcer le rôle admin"""
    user = User.query.get(session['user_id'])
    user.role = 'admin'
    user.is_active = True
    db.session.commit()
    
    # Mettre à jour la session
    session['role'] = 'admin'
    
    flash(f'Rôle admin forcé pour {user.username}', 'success')
    return redirect(url_for('debug_user'))

@app.route('/logout')
def logout():
    # Supprimer les données de session
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('role', None)
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('index'))

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        user = User.query.get(session['user_id'])

        if not check_password_hash(user.password, current_password):
            flash('Mot de passe actuel incorrect.', 'danger')
            return redirect(url_for('change_password'))

        if new_password != confirm_password:
            flash('Les nouveaux mots de passe ne correspondent pas.', 'danger')
            return redirect(url_for('change_password'))

        user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
        db.session.commit()

        flash('Mot de passe mis à jour avec succès.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('change_password.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            token = serializer.dumps(user.email, salt='reset-password')
            link = url_for('reset_password', token=token, _external=True)

            msg = Message('Réinitialisation de votre mot de passe', recipients=[email])
            msg.body = f'Cliquez sur ce lien pour réinitialiser votre mot de passe : {link}'
            mail.send(msg)

        flash("Si l'adresse e-mail existe, un lien a été envoyé.", 'info')
        return redirect(url_for('login'))

    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='reset-password', max_age=3600)
    except:
        flash('Le lien est invalide ou expiré.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_password = request.form['password']
        user = User.query.filter_by(email=email).first()
        user.password = generate_password_hash(new_password)
        db.session.commit()
        flash('Mot de passe modifié avec succès.', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html')

# Commandes CLI pour la gestion de la base de données
from flask.cli import with_appcontext
import click
from flask_migrate import init as alembic_init, migrate as alembic_migrate, upgrade as alembic_upgrade

@app.cli.command("db-init")
@with_appcontext
def db_init():
    """Initialise Alembic (équivalent à flask db init)"""
    alembic_init()

@app.cli.command("db-migrate")
@click.option("--message", "-m", default="Migration")
@with_appcontext
def db_migrate(message):
    """Crée une migration (équivalent à flask db migrate -m ...)"""
    alembic_migrate(message=message)

@app.cli.command("db-upgrade")
@with_appcontext
def db_upgrade():
    """Applique la migration (équivalent à flask db upgrade)"""
    alembic_upgrade()

@app.cli.command('create-admin')
@with_appcontext
def create_admin():
    """Créer un compte administrateur."""
    username = input("Nom d'utilisateur admin: ")
    email = input("Email admin: ")
    password = input("Mot de passe admin: ")
    
    # Vérifier si l'utilisateur existe déjà
    if User.query.filter_by(username=username).first():
        print("Nom d'utilisateur déjà utilisé")
        return
    
    if User.query.filter_by(email=email).first():
        print("Email déjà utilisé")
        return
    
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    admin_user = User(username=username, email=email, password=hashed_password, role='admin')
    
    db.session.add(admin_user)
    db.session.commit()
    
    print(f"Administrateur {username} créé avec succès!")

@app.cli.command('init-db')
@with_appcontext
def init_db_command():
    """Créer les tables de base de données."""
    db.create_all()
    print('Base de données initialisée.')

@app.cli.command('list-users')
@with_appcontext
def list_users():
    """Lister tous les utilisateurs."""
    users = User.query.all()
    print("\n=== Liste des utilisateurs ===")
    for user in users:
        status = "Actif" if user.is_active else "Inactif"
        print(f"ID: {user.id} | Username: {user.username} | Email: {user.email} | Rôle: {user.role} | Statut: {status}")
    print(f"\nTotal: {len(users)} utilisateurs")

@app.cli.command('check-user')
@click.argument('username')
@with_appcontext
def check_user(username):
    """Vérifier les détails d'un utilisateur spécifique."""
    user = User.query.filter_by(username=username).first()
    if user:
        print(f"\n=== Détails de l'utilisateur {username} ===")
        print(f"ID: {user.id}")
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
        print(f"Rôle: {user.role}")
        print(f"is_admin(): {user.is_admin()}")
        print(f"is_coureur(): {user.is_coureur()}")
        print(f"Actif: {user.is_active}")
        print(f"Créé le: {user.created_at}")
    else:
        print(f"Utilisateur '{username}' non trouvé")

@app.cli.command('fix-admin-role')
@click.argument('username')
@with_appcontext
def fix_admin_role(username):
    """Forcer le rôle admin pour un utilisateur."""
    user = User.query.filter_by(username=username).first()
    if user:
        user.role = 'admin'
        user.is_active = True
        db.session.commit()
        print(f"Rôle admin forcé pour {username}")
        print(f"Nouveau rôle: {user.role}")
        print(f"is_admin(): {user.is_admin()}")
    else:
        print(f"Utilisateur '{username}' non trouvé")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Crée les tables si elles n'existent pas
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))