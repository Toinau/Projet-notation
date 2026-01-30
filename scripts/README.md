# Scripts Utilitaires

Ce dossier contient les scripts utilitaires pour la gestion et la configuration de l'application.

## 📧 Configuration Email Gmail

### `configure_gmail.py`
Script interactif pour configurer Gmail dans le fichier `.env`.

**Usage :**
```bash
python scripts/configure_gmail.py
# ou
python scripts/configure_gmail.py email password
```

### `fix_gmail_password.py`
Script pour corriger le mot de passe d'application Gmail dans le fichier `.env`.

**Usage :**
```bash
python scripts/fix_gmail_password.py
```

### `check_email_config.py`
Vérifie la configuration email actuelle.

**Usage :**
```bash
python scripts/check_email_config.py
```

### `test_email_config.py`
Teste l'envoi d'un email pour vérifier la configuration.

**Usage :**
```bash
python scripts/test_email_config.py
```

## 📞 Utilitaires

### `check_phone_numbers.py`
Vérifie et corrige les numéros de téléphone dans la base de données.

**Usage :**
```bash
python scripts/check_phone_numbers.py
```

### `activate_notifications.py`
Active les notifications pour les utilisateurs.

**Usage :**
```bash
python scripts/activate_notifications.py
```
