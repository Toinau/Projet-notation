# 🏃‍♂️ Application de Notation des Coureurs - Moyon Percy Vélo Club

Application Flask moderne pour la gestion et l'évaluation des coureurs du club de vélo, incluant un système complet de questionnaires, classements et commandes CLI.

## ✨ Fonctionnalités

### 🔐 Authentification et Sécurité
- **Inscription/Connexion** avec validation des données
- **Gestion des rôles** (admin/coureur) avec permissions
- **Validation des mots de passe** (complexité requise)
- **Validation des emails** (format regex)
- **Sessions sécurisées** avec expiration automatique
- **Réinitialisation de mot de passe** par email

### 👥 Gestion des Utilisateurs
- **Dashboard administrateur** avec statistiques complètes
- **Gestion complète des utilisateurs** (créer, modifier, supprimer)
- **Activation/désactivation** des comptes
- **Promotion/rétrogradation** des rôles
- **Interface coureur** dédiée avec statistiques personnelles
- **Identification par prénom/nom** (suppression du champ username)

### 📊 Système de Questionnaires et Évaluations
- **Création de questionnaires** par les administrateurs
- **Évaluation des coureurs** par leurs pairs (notes de 1 à 10)
- **Commentaires** sur les questionnaires
- **Statistiques détaillées** par course et par coureur
- **Classements** mensuels et annuels
- **Points Direct Vélo** intégrés au système de notation

### 🏆 Classements et Statistiques
- **Classement global** de la saison
- **Classement mensuel** avec sélecteur de mois
- **Statistiques par course** (moyennes, notes max/min)
- **Détails des points** par coureur
- **Historique des performances**

### 🛠️ Commandes CLI
- **Gestion de la base de données** (init, reset, stats)
- **Création d'utilisateurs** (interactif et par options)
- **Administration des comptes** (liste, vérification, modification)
- **Génération de comptes de test** pour les essais
- **Validation automatique** des données

### 💾 Sauvegarde et Restauration
- **Scripts de sauvegarde** automatique du projet
- **Restauration** de sauvegardes
- **Sauvegarde vers GitHub** intégrée

## 🚀 Installation

### Prérequis
- Python 3.8+
- pip
- Git

### Installation
```bash
# Cloner le projet
git clone https://github.com/Toinau/Projet-notation.git
cd Projet-notation

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
cp env.example .env
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
flask create-user --prenom Jean --nom Dupont --email jean@example.com --password Secret123 --role admin

# Lister tous les utilisateurs
flask list-users

# Vérifier un utilisateur
flask check-user Jean Dupont

# Forcer le rôle admin
flask fix-admin-role Jean Dupont

# Supprimer un utilisateur
flask delete-user Jean Dupont --force

# Activer/désactiver un utilisateur
flask toggle-user-status Jean Dupont

# Changer le rôle
flask change-user-role Jean Dupont --role admin
```

#### 🧪 Génération de Comptes de Test
```bash
# Générer des utilisateurs fictifs pour les tests
python populate_fake_users.py

# Créer des comptes de test spécifiques
python test_multiple_accounts.py
```

## 📁 Structure du Projet

```
Projet-notation/
├── run.py                    # Application principale
├── config.py                # Configuration
├── requirements.txt         # Dépendances
├── env.example             # Exemple de variables d'environnement
├── CLI_COMMANDS.md         # Documentation des commandes CLI
├── README.md              # Ce fichier
├── backup_project.py      # Script de sauvegarde
├── restore_backup.py      # Script de restauration
├── populate_fake_users.py # Génération de comptes de test
├── test_multiple_accounts.py # Comptes de test spécifiques
├── app/                   # Application Flask
│   ├── __init__.py       # Initialisation de l'app
│   ├── models.py         # Modèles de base de données
│   ├── routes.py         # Routes de l'application
│   ├── cli.py           # Commandes CLI
│   └── decorators.py    # Décorateurs d'authentification
├── templates/            # Templates HTML
│   ├── admin/           # Templates administrateur
│   ├── coureur/         # Templates coureur
│   └── *.html           # Templates généraux
├── static/              # Fichiers statiques (CSS, JS)
├── migrations/          # Migrations de base de données
├── backups/            # Sauvegardes du projet
└── instance/           # Fichiers d'instance (base de données)
```

## 🔧 Fonctionnalités Récentes

### ✅ Refonte de la Gestion des Utilisateurs
- **Suppression du champ username** : Utilisation de prénom/nom uniquement
- **Email comme identifiant** : Connexion par email
- **Interface simplifiée** : Affichage cohérent prénom/nom partout

### 📊 Système de Questionnaires Avancé
- **Création de questionnaires** par les admins
- **Évaluation croisée** des coureurs
- **Commentaires** sur les questionnaires
- **Statistiques détaillées** (notes moyennes, max, min)
- **Classements** avec points Direct Vélo

### 🏆 Classements et Statistiques
- **Classement global** de la saison
- **Classement mensuel** avec sélecteur
- **Messages informatifs** quand aucune course
- **Détails des points** par course

### 🛡️ Sécurité et Validation
- **Validation des données** : Email, mot de passe, prénom/nom
- **Gestion des erreurs** : Try/catch avec rollback
- **Logging** : Traçabilité des actions
- **Sanitisation** : Nettoyage des entrées utilisateur

### 🎨 Interface Améliorée
- **Thème sombre** cohérent
- **Messages d'erreur** clairs et informatifs
- **Feedback utilisateur** : Confirmations et notifications
- **Responsive design** pour mobile

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

### Prénom et Nom
- Minimum 2 caractères
- Caractères autorisés : lettres, espaces, tirets
- Validation côté serveur

## 📊 Base de Données

### Modèle User (Nouveau)
```python
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prenom = db.Column(db.String(100), nullable=False)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='coureur')
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### Modèle Questionnaire
```python
class Questionnaire(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(200), nullable=False)
    course_date = db.Column(db.Date, nullable=False)
    direct_velo_points = db.Column(db.Integer, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
```

### Modèle QuestionnaireResponse
```python
class QuestionnaireResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    questionnaire_id = db.Column(db.Integer, db.ForeignKey('questionnaire.id', ondelete='CASCADE'))
    evaluator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    evaluated_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    rating = db.Column(db.Integer, nullable=False)  # Note de 1 à 10
```

## 🐛 Débogage

### Routes de Debug (à supprimer en production)
- `/debug-user` : Informations de debug utilisateur
- `/force-admin-role` : Forcer le rôle admin
- `/debug-ranking` : Debug des classements

### Logs
Les erreurs sont loggées avec `app.logger.error()` pour faciliter le débogage.

## 🚀 Déploiement

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
- Moyon Percy Vélo Club pour l'inspiration

---

**Version : 3.0** - Application complète de notation des coureurs avec système de questionnaires et classements 