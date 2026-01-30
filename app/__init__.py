import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from itsdangerous import URLSafeTimedSerializer
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
serializer = None

def create_app():
    # Forcer le chemin du dossier templates et static à la racine du projet
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    template_dir = os.path.join(BASE_DIR, 'templates')
    static_dir = os.path.join(BASE_DIR, 'static')
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

    app.config.from_object('config.Config')
    
    # En développement : rechargement auto des templates ; en production : ne pas écraser DEBUG
    if not app.config.get('DEBUG'):
        app.config['TEMPLATES_AUTO_RELOAD'] = False
    else:
        app.config['TEMPLATES_AUTO_RELOAD'] = True
    
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    global serializer
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

    # Initialisation Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    from app.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .routes import main_bp
    app.register_blueprint(main_bp)

    from .cli import register_cli
    register_cli(app)

    # Gestion des erreurs HTTP (évite d'exposer des traces en production)
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Erreur 500: {error}")
        return render_template('errors/500.html'), 500

    return app