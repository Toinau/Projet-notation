# Commandes CLI de l'Application

Ce document décrit toutes les commandes CLI disponibles pour gérer votre application Flask.

## 🚀 Installation et Configuration

Assurez-vous que votre fichier `.flaskenv` contient :
```
FLASK_APP=run.py
FLASK_ENV=development
```

## 📋 Commandes Disponibles

### 🔧 Gestion de la Base de Données

#### Initialiser la base de données
```bash
flask init-db
```
Crée toutes les tables nécessaires dans la base de données.

#### Réinitialiser complètement la base de données
```bash
flask reset-db
```
⚠️ **ATTENTION** : Supprime toutes les données existantes !

Pour forcer sans confirmation :
```bash
flask reset-db --force
```

#### Afficher les statistiques de la base de données
```bash
flask db-stats
```
Affiche le nombre total d'utilisateurs, coureurs, administrateurs, etc.

### 👥 Gestion des Utilisateurs

#### Créer un administrateur (interactif)
```bash
flask create-admin
```
Demande interactivement le nom d'utilisateur, email et mot de passe.

#### Créer un utilisateur avec options
```bash
flask create-user --username john --email john@example.com --password secret123 --role admin
```

Options disponibles :
- `--username` : Nom d'utilisateur (requis)
- `--email` : Adresse email (requise)
- `--password` : Mot de passe (requis, masqué lors de la saisie)
- `--role` : Rôle (coureur ou admin, défaut: coureur)

#### Lister tous les utilisateurs
```bash
flask list-users
```
Affiche tous les utilisateurs avec leurs détails.

#### Vérifier un utilisateur spécifique
```bash
flask check-user username
```
Affiche les détails complets d'un utilisateur.

#### Forcer le rôle admin pour un utilisateur
```bash
flask fix-admin-role username
```
Change le rôle d'un utilisateur en admin et l'active.

#### Supprimer un utilisateur
```bash
flask delete-user username
```
Demande confirmation avant suppression.

Pour forcer sans confirmation :
```bash
flask delete-user username --force
```

#### Activer/Désactiver un utilisateur
```bash
flask toggle-user-status username
```
Bascule le statut actif/inactif d'un utilisateur.

#### Changer le rôle d'un utilisateur
```bash
flask change-user-role username --role admin
```
Change le rôle d'un utilisateur (coureur ou admin).

## 🎯 Exemples d'Utilisation

### Créer un premier administrateur
```bash
# 1. Initialiser la base de données
flask init-db

# 2. Créer un administrateur
flask create-admin
# Suivre les instructions interactives
```

### Gérer plusieurs utilisateurs
```bash
# Créer des utilisateurs avec des rôles différents
flask create-user --username alice --email alice@example.com --password pass123 --role coureur
flask create-user --username bob --email bob@example.com --password pass456 --role admin

# Lister tous les utilisateurs
flask list-users

# Vérifier un utilisateur spécifique
flask check-user alice

# Promouvoir un coureur en admin
flask change-user-role alice --role admin
```

### Maintenance de la base de données
```bash
# Voir les statistiques
flask db-stats

# Désactiver un utilisateur problématique
flask toggle-user-status username

# Supprimer un utilisateur
flask delete-user username

# Réinitialiser complètement (⚠️ ATTENTION)
flask reset-db --force
```

## 🔍 Dépannage

### Problème : "Command not found"
Assurez-vous que :
1. Vous êtes dans le bon répertoire
2. Le fichier `.flaskenv` existe et contient `FLASK_APP=run.py`
3. L'environnement virtuel est activé

### Problème : "No module named 'flask'"
Activez votre environnement virtuel :
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### Problème : Erreur de base de données
Réinitialisez la base de données :
```bash
flask reset-db --force
flask init-db
```

## 📝 Notes Importantes

- Toutes les commandes nécessitent que l'application Flask soit correctement configurée
- Les mots de passe sont automatiquement hashés avec `pbkdf2:sha256`
- Les commandes de suppression demandent confirmation par défaut
- Utilisez `--force` pour éviter les confirmations interactives
- Les commandes CLI sont utiles pour l'administration et le développement 