from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Création de l'application Flask
app = Flask(__name__)

# Configuration de la base de données (SQLite ici)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialisation de l'extension SQLAlchemy
db = SQLAlchemy(app)

# Import des modèles pour que SQLAlchemy les reconnaisse
from app import models
