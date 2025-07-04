import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from itsdangerous import URLSafeTimedSerializer

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
    
    # Activer le mode debug pour le rechargement automatique
    app.config['DEBUG'] = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    global serializer
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

    from .routes import main_bp
    app.register_blueprint(main_bp)

    from .cli import register_cli
    register_cli(app)

    return app 