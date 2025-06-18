import os
from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config.from_object('config.Config')

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

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')

    def __repr__(self):
        return f'<User {self.username}>'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
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
        new_user = User(username=username, email=email, password=hashed_password)
        
        # Ajouter l'utilisateur à la base de données
        db.session.add(new_user)
        db.session.commit()
        
        flash('Votre compte a été créé avec succès!', 'success')
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
        
        # Si les identifiants sont valides, créer une session pour l'utilisateur
        session.permanent = remember
        session['user_id'] = user.id
        session['username'] = user.username
        
        flash(f'Bienvenue, {user.username}!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    # Vérifier si l'utilisateur est connecté
    if 'user_id' not in session:
        flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
        return redirect(url_for('login'))
    
    return render_template('dashboard.html', username=session['username'])

@app.route('/logout')
def logout():
    # Supprimer les données de session
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('index'))

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        flash('Veuillez vous connecter pour changer votre mot de passe.', 'warning')
        return redirect(url_for('login'))

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

# Commande CLI pour créer les tables
@app.cli.command('init-db')
def init_db_command():
    """Créer les tables de base de données."""
    db.create_all()
    print('Base de données initialisée.')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Crée les tables si elles n'existent pas
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

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
