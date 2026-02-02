import os
from dotenv import load_dotenv

# Charger .env puis .env.local (les variables de .env.local écrasent celles de .env)
# En local : créez .env.local avec FLASK_ENV=development et DATABASE_URL= pour utiliser SQLite
# Sur le serveur : pas de .env.local → seul .env est utilisé (PostgreSQL de prod)
load_dotenv()
_env_local = os.path.join(os.path.dirname(__file__), '.env.local')
if os.path.isfile(_env_local):
    load_dotenv(_env_local, override=True)

# Détection de l'environnement de production
FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
IS_PRODUCTION = FLASK_ENV == 'production' or os.environ.get('FLASK_DEBUG', 'True').lower() == 'false'

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Configuration avancée pour la sécurité et la persistance des sessions Flask/Flask-Login
    SESSION_COOKIE_NAME = "session"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = IS_PRODUCTION  # True en production HTTPS

    REMEMBER_COOKIE_NAME = "remember_token"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = IS_PRODUCTION  # True en production HTTPS

    # Durée de la session (exemple : 7 jours)
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24 * 7  # en secondes (ici 7 jours)
    
    # Configuration de la base de données
    # En production, utilise PostgreSQL via DATABASE_URL
    # En développement, utilise SQLite
    _database_url = os.environ.get('DATABASE_URL')
    if IS_PRODUCTION and _database_url:
        _db_uri = _database_url
    else:
        basedir = os.path.abspath(os.path.dirname(__file__))
        sqlite_path = os.path.join(basedir, 'instance', 'app.db')
        # Crée le dossier 'instance' s'il n'existe pas
        os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
        _db_uri = _database_url or f"sqlite:///{sqlite_path}"
    
    # Fix pour PostgreSQL (remplace postgres:// par postgresql://)
    if _db_uri and _db_uri.startswith("postgres://"):
        _db_uri = _db_uri.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_DATABASE_URI = _db_uri
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Mode debug (désactivé en production)
    DEBUG = not IS_PRODUCTION
    TESTING = False
    
    # Configuration email
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() in ['true', 'on', '1']
    MAIL_USE_TLS = False if MAIL_USE_SSL else (os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1'])
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Configuration Twilio pour SMS
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')

    # Configuration Free Mobile pour SMS
    FREE_MOBILE_USER = os.environ.get('FREE_MOBILE_USER')
    FREE_MOBILE_API_KEY = os.environ.get('FREE_MOBILE_API_KEY')
    
    # Configuration de l'URL de l'application pour les liens dans les emails
    APP_URL = os.environ.get('APP_URL', 'http://localhost:5000')