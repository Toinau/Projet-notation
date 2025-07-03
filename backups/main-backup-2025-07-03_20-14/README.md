# 🏃‍♂️ Application de Gestion des Utilisateurs

Application Flask moderne pour la gestion des utilisateurs avec différents rôles (admin et coureur), incluant un système complet de commandes CLI.

## ✨ Fonctionnalités

### 🔐 Authentification et Sécurité
- **Inscription/Connexion** avec validation des données
- **Gestion des rôles** (admin/coureur) avec permissions
- **Validation des mots de passe** (complexité requise)
- **Validation des emails** (format regex)
- **Sessions sécurisées** avec expiration automatique
- **Réinitialisation de mot de passe** par email

### 👥 Gestion des Utilisateurs
- **Dashboard administrateur** avec statistiques
- **Gestion complète des utilisateurs** (créer, modifier, supprimer)
- **Activation/désactivation** des comptes
- **Promotion/rétrogradation** des rôles
- **Interface coureur** dédiée

### 🛠️ Commandes CLI
- **Gestion de la base de données** (init, reset, stats)
- **Création d'utilisateurs** (interactif et par options)
- **Administration des comptes** (liste, vérification, modification)
- **Validation automatique** des données

## 🚀 Installation

### Prérequis
- Python 3.8+
- pip

### Installation
```bash
# Cloner le projet
git clone <votre-repo>
cd projet-notation

# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos configurations
```

### Configuration
Créer un fichier `.env` avec :
```env
SECRET_KEY=votre-clé-secrète-très-sécurisée
MAIL_USERNAME=votre-email@gmail.com
MAIL_PASSWORD=votre-mot-de-passe-app
MAIL_DEFAULT_SENDER=votre-email@gmail.com
```

## 🎯 Utilisation

### Démarrage de l'application
```bash
# Mode développement
python run.py

# Ou avec Flask CLI
flask run
```

### Commandes CLI disponibles

#### 🔧 Gestion de la Base de Données
```bash
# Initialiser la base de données
flask init-db

# Réinitialiser complètement (⚠️ ATTENTION)
flask reset-db --force

# Voir les statistiques
flask db-stats
```

#### 👥 Gestion des Utilisateurs
```bash
# Créer un administrateur (interactif)
flask create-admin

# Créer un utilisateur avec options
flask create-user --username john --email john@example.com --password Secret123 --role admin

# Lister tous les utilisateurs
flask list-users

# Vérifier un utilisateur
flask check-user username

# Forcer le rôle admin
flask fix-admin-role username

# Supprimer un utilisateur
flask delete-user username --force

# Activer/désactiver un utilisateur
flask toggle-user-status username

# Changer le rôle
flask change-user-role username --role admin
```

## 📁 Structure du Projet

```
projet-notation/
├── run.py                 # Application principale
├── config.py             # Configuration
├── requirements.txt      # Dépendances
├── .flaskenv            # Variables d'environnement Flask
├── .env                 # Variables d'environnement (à créer)
├── CLI_COMMANDS.md      # Documentation des commandes CLI
├── README.md           # Ce fichier
├── templates/          # Templates HTML
│   ├── admin/         # Templates admin
│   ├── coureur/       # Templates coureur
│   └── *.html         # Templates généraux
├── static/            # Fichiers statiques (CSS, JS)
├── migrations/        # Migrations de base de données
├── backups/          # Sauvegardes
└── instance/         # Fichiers d'instance (base de données)
```

## 🔧 Améliorations Apportées

### ✅ Code Nettoyé
- **Suppression des doublons** : Fichiers CLI redondants supprimés
- **Structure simplifiée** : Un seul fichier principal `run.py`
- **Organisation claire** : Sections bien définies avec commentaires

### 🛡️ Sécurité Renforcée
- **Validation des données** : Email, mot de passe, nom d'utilisateur
- **Gestion des erreurs** : Try/catch avec rollback
- **Logging** : Traçabilité des actions
- **Sanitisation** : Nettoyage des entrées utilisateur

### 🎨 Interface Améliorée
- **Messages d'erreur** : Plus clairs et informatifs
- **Feedback utilisateur** : Confirmations et notifications
- **Validation côté serveur** : Double vérification

### 🚀 Performance
- **Optimisation des requêtes** : Requêtes SQL optimisées
- **Gestion de session** : Sessions sécurisées
- **Cache** : Configuration optimisée

## 🔍 Validation des Données

### Mot de Passe
- Minimum 8 caractères
- Au moins une majuscule
- Au moins une minuscule
- Au moins un chiffre

### Email
- Format valide (regex)
- Conversion en minuscules
- Vérification d'unicité

### Nom d'Utilisateur
- Minimum 3 caractères
- Caractères autorisés : lettres, chiffres, underscore
- Vérification d'unicité

## 🐛 Débogage

### Routes de Debug (à supprimer en production)
- `/debug-user` : Informations de debug utilisateur
- `/force-admin-role` : Forcer le rôle admin

### Logs
Les erreurs sont loggées avec `app.logger.error()` pour faciliter le débogage.

## 📊 Base de Données

### Modèle User
```python
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='coureur')
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### Migrations
```bash
# Initialiser les migrations
flask db init

# Créer une migration
flask db migrate -m "Description"

# Appliquer les migrations
flask db upgrade
```

## 🚀 Déploiement

### Railway
Le projet est configuré pour Railway avec :
- `Procfile` : Configuration du serveur
- `railway.toml` : Configuration Railway
- `wsgi.py` : Point d'entrée WSGI

### Variables d'Environnement de Production
```env
DATABASE_URL=postgresql://...
SECRET_KEY=clé-secrète-production
MAIL_USERNAME=email-production
MAIL_PASSWORD=mot-de-passe-production
```

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 👨‍💻 Auteur

**Antoine Piedagnel**
- Email: antoine.piedagnel@gmail.com
- GitHub: [@Toinau](https://github.com/Toinau)

## 🙏 Remerciements

- Flask et son écosystème
- SQLAlchemy pour l'ORM
- Click pour les commandes CLI
- Bootstrap pour l'interface utilisateur

---

**Version : 2.0** - Application refactorisée et améliorée 