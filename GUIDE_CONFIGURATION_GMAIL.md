# 📧 Guide de Configuration Gmail pour l'Envoi d'Emails

## ⚠️ Problème : Erreur d'authentification Gmail

Si vous rencontrez l'erreur :
```
535-5.7.8 Username and Password not accepted
```

Cela signifie que Gmail rejette vos identifiants. **Gmail ne permet plus l'utilisation du mot de passe normal du compte** pour les applications tierces.

## ✅ Solution : Utiliser un Mot de Passe d'Application

Gmail nécessite maintenant un **"Mot de passe d'application"** (App Password) pour les applications qui envoient des emails via SMTP.

### 📋 Étapes pour créer un Mot de Passe d'Application Gmail

#### Étape 1 : Activer l'Authentification à Deux Facteurs (2FA)

**⚠️ OBLIGATOIRE** : Vous DEVEZ avoir l'authentification à deux facteurs activée pour créer un mot de passe d'application.

1. Allez sur [https://myaccount.google.com/security](https://myaccount.google.com/security)
2. Dans la section **"Connexion à Google"**, cliquez sur **"Validation en deux étapes"**
3. Suivez les instructions pour activer la 2FA (nécessaire pour créer un mot de passe d'application)

#### Étape 2 : Créer un Mot de Passe d'Application

1. Allez sur [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
   - Ou : Google Account > Sécurité > Validation en deux étapes > Mots de passe des applications

2. **Supprimez les anciens mots de passe d'application** (s'il y en a) pour éviter la confusion

3. Créez un nouveau mot de passe :
   - **Application** : "Mail"
   - **Appareil** : "Autre (nom personnalisé)" et entrez "Flask App" ou un nom de votre choix
   - Cliquez sur **"Générer"**

4. **Copiez le mot de passe généré** :
   - Il sera affiché comme : `abcd efgh ijkl mnop` (avec des espaces)
   - **IMPORTANT** : Supprimez TOUS les espaces → `abcdefghijklmnop`
   - Le mot de passe final doit faire exactement **16 caractères SANS espaces**

#### Étape 3 : Configurer dans votre Application

**Option A : Utiliser le script de configuration automatique (RECOMMANDÉ)**

```bash
python configure_gmail.py
```

Le script vous demandera :
- Votre adresse email Gmail
- Le mot de passe d'application (les 16 caractères générés)

**Option B : Utiliser le script de correction**

```bash
python fix_gmail_password.py
```

**Option C : Configuration manuelle dans le fichier `.env`**

Éditez votre fichier `.env` et configurez :

```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=votre-email@gmail.com
MAIL_PASSWORD=votre-mot-de-passe-application-16-caracteres
MAIL_DEFAULT_SENDER=votre-email@gmail.com
```

⚠️ **IMPORTANT** :
- Utilisez le **mot de passe d'application** (16 caractères), PAS votre mot de passe Gmail normal
- Le mot de passe d'application ne contient PAS d'espaces
- Si vous copiez-collez, vérifiez qu'il n'y a pas d'espaces

#### Étape 4 : REDÉMARRER l'Application Flask

**⚠️ CRITIQUE** : Vous DEVEZ redémarrer l'application pour que les changements soient pris en compte.

1. **Arrêtez l'application Flask** :
   - Dans le terminal où elle tourne, appuyez sur `Ctrl+C`
   - Attendez que l'application s'arrête complètement

2. **Relancez l'application** :
   ```bash
   python run.py
   ```

## 🔍 Vérification et Tests

### Vérifier la configuration actuelle
```bash
python check_email_config.py
```

### Tester l'envoi d'email
```bash
python test_email_config.py
```

Entrez votre adresse email pour recevoir un email de test.

## ❓ Problèmes Courants et Solutions

### "Username and Password not accepted"
- ✅ Vérifiez que vous utilisez un **mot de passe d'application**, pas votre mot de passe Gmail
- ✅ Vérifiez qu'il n'y a pas d'espaces dans le mot de passe
- ✅ Vérifiez que l'authentification à deux facteurs est activée
- ✅ **Redémarrez l'application Flask** après modification du `.env`

### "Le mot de passe fait X caractères (devrait être 16)"
- ✅ Supprimez tous les espaces du mot de passe
- ✅ Vérifiez que vous avez bien copié les 16 caractères

### "L'authentification à deux facteurs n'est pas activée"
- ✅ Activez-la d'abord sur : https://myaccount.google.com/security
- ✅ Puis créez le mot de passe d'application

### "L'erreur persiste après redémarrage"
- ✅ Vérifiez que vous utilisez bien un **mot de passe d'application** et non votre mot de passe Gmail normal
- ✅ Créez un nouveau mot de passe d'application (supprimez l'ancien d'abord)
- ✅ Vérifiez qu'il n'y a pas d'espaces dans le fichier .env
- ✅ Vérifiez que le fichier .env est bien à la racine du projet

### "Less secure app access"
- Cette option est dépréciée par Google
- Utilisez plutôt un **mot de passe d'application** (voir ci-dessus)

### L'email n'arrive pas
- Vérifiez votre dossier spam
- Vérifiez que l'adresse email de destination est correcte
- Vérifiez les logs de l'application pour voir les erreurs détaillées

## 📞 Si rien ne fonctionne

1. Vérifiez que votre compte Gmail n'a pas de restrictions :
   - Allez sur : https://myaccount.google.com/security
   - Vérifiez qu'il n'y a pas d'alertes de sécurité

2. Essayez de créer le mot de passe d'application depuis un autre navigateur

3. Vérifiez les logs de l'application pour des erreurs plus détaillées

## 📚 Ressources

- [Créer un mot de passe d'application Google](https://support.google.com/accounts/answer/185833)
- [Sécurité du compte Google](https://myaccount.google.com/security)
