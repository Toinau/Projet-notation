# Mise à jour du .env en production

Le fichier `.env` n’est **pas** versionné sur GitHub (sécurité). Pour changer la config (Gmail, base de données, etc.) en production, il faut modifier le `.env` **directement sur le serveur**.

## Étapes

### 1. Se connecter au serveur

Depuis PowerShell (Windows) ou un terminal :

```bash
ssh root@VOTRE_IP_SERVEUR
```

(Remplacez `VOTRE_IP_SERVEUR` par l’IP de votre VPS Ionos.)

### 2. Aller dans le dossier de l’application

```bash
cd /var/www/Projet-notation
```

### 3. Éditer le fichier .env

```bash
nano .env
```

- Modifiez les lignes concernées (ex. `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER` pour Gmail).
- Pour enregistrer : **Ctrl+O** puis **Entrée**.
- Pour quitter : **Ctrl+X**.

### 4. Redémarrer l’application

Sinon l’ancienne config reste en mémoire :

```bash
supervisorctl restart notation-app
```

### 5. Vérifier

```bash
supervisorctl status notation-app
```

Vous devez voir `notation-app RUNNING`.

---

## Variables à mettre à jour selon le cas

| Besoin | Variables à modifier |
|--------|----------------------|
| **Changer le compte Gmail** | `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER` |
| Changer la base de données | `DATABASE_URL` |
| Changer l’URL du site | `APP_URL`, `DOMAIN` |
| Régénérer la clé secrète | `SECRET_KEY` |

Pour Gmail, utilisez toujours un **mot de passe d’application** (Sécurité Google → Mots de passe des applications), pas le mot de passe du compte.

---

## Option : préparer le contenu en local

Vous pouvez noter les nouvelles valeurs dans un fichier **sur votre PC** (sans le commiter), puis les recopier dans `nano .env` sur le serveur. Ne mettez jamais de vrais mots de passe dans un fichier versionné.

Voir aussi : [GUIDE_DEPLOIEMENT_IONOS.md](GUIDE_DEPLOIEMENT_IONOS.md) — section « Si vous avez modifié le fichier .env ».
