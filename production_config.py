import os
from dotenv import load_dotenv

load_dotenv()

class ProductionConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'change-me-in-production-very-secure-key'
    
    # Configuration sécurisée pour la production
    SESSION_COOKIE_NAME = "session"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = True  # HTTPS en production

    REMEMBER_COOKIE_NAME = "remember_token"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = True  # HTTPS en production

    # Durée de la session (7 jours)
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24 * 7
    
    # Configuration PostgreSQL pour la production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        "postgresql://notation_user:notation_password_2024@localhost/notation_app"
    
    # Fix pour PostgreSQL
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuration email
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() in ['true', 'on', '1']
    MAIL_USE_TLS = False if MAIL_USE_SSL else (os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1'])
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # URL de l'application (liens dans les emails)
    APP_URL = os.environ.get('APP_URL', 'https://votre-domaine.com')
    
    # Mode production
    DEBUG = False
    TESTING = False 