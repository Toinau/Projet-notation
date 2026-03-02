# 🚀 Guide de Déploiement sur Ionos - Application Flask

Ce guide vous explique étape par étape comment déployer votre application Flask sur un VPS Ionos pour qu'elle soit accessible 24h/24.

## 📋 Table des matières

1. [Prérequis](#prérequis)
2. [Choix : Domaine principal ou sous-domaine ?](#choix--domaine-principal-ou-sous-domaine-)
3. [Étape 1 : Achat et configuration du VPS Ionos](#étape-1--achat-et-configuration-du-vps-ionos)
4. [Étape 2 : Connexion au serveur](#étape-2--connexion-au-serveur)
5. [Étape 3 : Installation des dépendances](#étape-3--installation-des-dépendances)
6. [Étape 4 : Configuration de la base de données](#étape-4--configuration-de-la-base-de-données)
7. [Étape 5 : Déploiement de l'application](#étape-5--déploiement-de-lapplication)
8. [Étape 6 : Configuration de l'environnement](#étape-6--configuration-de-lenvironnement)
9. [Étape 7 : Configuration de Gunicorn et Supervisor](#étape-7--configuration-de-gunicorn-et-supervisor)
10. [Étape 8 : Configuration de Nginx](#étape-8--configuration-de-nginx)
11. [Étape 9 : Configuration SSL/HTTPS](#étape-9--configuration-sslhttps)
12. [Étape 10 : Configuration du firewall](#étape-10--configuration-du-firewall)
13. [Vérification et tests](#vérification-et-tests)
14. [Mise à jour de l'application](#mise-à-jour-de-lapplication)
15. [Dépannage](#dépannage)
16. [Sauvegarde de la base de données](#sauvegarde-de-la-base-de-données)

---

## Prérequis

- Un compte Ionos
- Un domaine (optionnel mais recommandé)
- Accès SSH à votre machine locale
- Les identifiants de votre application (email Gmail, etc.)

**⚠️ Note importante** : Ce guide est conçu pour un **VPS Linux (Ubuntu)**. Un VPS Windows n'est **pas recommandé** et nécessiterait une configuration complètement différente (et plus coûteuse).

---

## Choix : Domaine principal ou sous-domaine ?

Avant de commencer, vous devez décider où héberger votre application :

### Option 1 : Domaine principal

- **URL** : `https://votre-domaine.com`
- **Avantages** : URL courte et directe
- **Inconvénients** : Prend le domaine principal (si vous avez déjà un site web)

### Option 2 : Sous-domaine (Recommandé) ✅

- **URL** : `https://app.votre-domaine.com` ou `https://notation.votre-domaine.com`
- **Avantages** :
  - ✅ Ne perturbe pas votre site principal (si vous en avez un)
  - ✅ Plus professionnel et organisé
  - ✅ Permet d'héberger plusieurs applications sur le même serveur
  - ✅ Plus facile à mémoriser
- **Inconvénients** : Aucun réel inconvénient

**Recommandation** : Utilisez un sous-domaine comme `app.votre-domaine.com` ou `notation.votre-domaine.com`

**Exemples de sous-domaines courants** :

- `app.votre-domaine.com` - Application principale
- `notation.votre-domaine.com` - Application de notation
- `admin.votre-domaine.com` - Interface d'administration
- `api.votre-domaine.com` - API (si vous en avez une)

Le guide couvre les deux options. Suivez simplement les instructions correspondantes à votre choix.

---

## Étape 1 : Achat et configuration du VPS Ionos

### 1.1 Achat du VPS

1. **Allez sur** : https://www.ionos.fr/serveurs/vps
2. **Choisissez un plan** :
   - **VPS S** (recommandé pour commencer) : 2 vCPU, 4 GB RAM, 80 GB SSD (~5€/mois)
   - **VPS M** (si vous avez beaucoup d'utilisateurs) : 4 vCPU, 8 GB RAM, 160 GB SSD (~10€/mois)
3. **Système d'exploitation** : **Choisissez Linux (Ubuntu 22.04 LTS ou 24.04)** ⚠️

**⚠️ Important : Linux obligatoire, pas Windows !**

**Pourquoi Linux ?**

- ✅ **Gratuit** : Pas de licence Windows à payer (~15-20€/mois en plus)
- ✅ **Performance** : Meilleures performances pour les serveurs web
- ✅ **Compatible** : Tous les outils nécessaires (Nginx, Gunicorn, PostgreSQL) sont conçus pour Linux
- ✅ **Sécurité** : Plus sécurisé et stable pour les serveurs
- ✅ **Communauté** : Large support et documentation
- ✅ **Scripts** : Tous les scripts de ce guide sont pour Linux

**Windows ne convient pas car** :

- ❌ Coût supplémentaire important (licence Windows Server)
- ❌ Configuration beaucoup plus complexe
- ❌ Nginx et Gunicorn ne sont pas optimisés pour Windows
- ❌ Les scripts de déploiement ne fonctionneraient pas
- ❌ Performance moindre pour les applications web

**Recommandation** : Choisissez **Ubuntu 22.04 LTS** (ou 24.04 si disponible)

4. **Finalisez la commande**

### 1.2 Récupération des informations

Après l'achat, vous recevrez par email :

- **Adresse IP** du serveur (ex: `123.456.789.012`)
- **Nom d'utilisateur** : `root`
- **Mot de passe** temporaire (à changer immédiatement)

### 1.3 Configuration initiale

1. Connectez-vous au **Panel Ionos**
2. Allez dans **Serveurs** > **Votre VPS**
3. Notez l'**adresse IP** et le **mot de passe root**

---

## Étape 2 : Connexion au serveur

### 2.1 Depuis Windows (PowerShell)

```powershell
# Installer OpenSSH si nécessaire
# Puis se connecter
ssh root@82.165.129.123
```

### 2.2 Depuis Linux/Mac

```bash
ssh root@VOTRE_IP_SERVEUR
```

### 2.3 Première connexion

- À la première connexion, acceptez la clé SSH (tapez `yes`)
- Entrez le mot de passe temporaire
- **Changez immédiatement le mot de passe** :
  ```bash
  passwd
  ```

---

## Étape 3 : Installation des dépendances

Une fois connecté au serveur, exécutez ces commandes :

```bash
# Mise à jour du système
apt update && apt upgrade -y

# Installation des dépendances système
apt install -y python3 python3-pip python3-venv nginx git supervisor postgresql postgresql-contrib ufw

# Vérification des versions
python3 --version  # Doit afficher Python 3.10 ou supérieur
nginx -v
postgresql --version
```

---

## Étape 4 : Configuration de la base de données

### 4.1 Configuration de PostgreSQL

```bash
# Passer en utilisateur postgres
sudo -u postgres psql

# Dans le shell PostgreSQL, exécutez :
CREATE DATABASE notation_app;
CREATE USER notation_user WITH PASSWORD 'VOTRE_MOT_DE_PASSE_SECURISE';
GRANT ALL PRIVILEGES ON DATABASE notation_app TO notation_user;
ALTER USER notation_user CREATEDB;
\q
```

**⚠️ Important** : Remplacez `VOTRE_MOT_DE_PASSE_SECURISE` par un mot de passe fort (minimum 16 caractères, lettres, chiffres, symboles).

### 4.2 Test de connexion

```bash
# Tester la connexion
sudo -u postgres psql -d notation_app -U notation_user
# Entrez le mot de passe que vous avez créé
# Tapez \q pour quitter
```

---

## Étape 5 : Déploiement de l'application

### 5.1 Clonage du projet

```bash
# Créer le dossier web
mkdir -p /var/www
cd /var/www

# Cloner le projet depuis GitHub
git clone https://github.com/Toinau/Projet-notation.git
cd Projet-notation
```

### 5.2 Configuration de l'environnement Python

```bash
# Créer l'environnement virtuel
python3 -m venv venv

# Activer l'environnement
source venv/bin/activate

# Mettre à jour pip
pip install --upgrade pip

# Installer les dépendances
pip install -r requirements.txt
```

### 5.3 Configuration des permissions

```bash
# Donner les permissions appropriées
chown -R www-data:www-data /var/www/Projet-notation
chmod -R 755 /var/www/Projet-notation
```

---

## Étape 6 : Configuration de l'environnement

### 6.1 Création du fichier .env

```bash
cd /var/www/Projet-notation

# Copier le fichier d'exemple
cp deploy/production.env.example .env

# Éditer le fichier
nano .env
```

### 6.2 Contenu du fichier .env

```env
# Clé secrète (générez-en une avec : python -c "import secrets; print(secrets.token_hex(32))")
SECRET_KEY=votre-clé-secrète-très-longue-et-aléatoire-générée-avec-secrets-token-hex

# Configuration email (Gmail)
MAIL_USERNAME=votre-email@gmail.com
MAIL_PASSWORD=votre-mot-de-passe-app-gmail
MAIL_DEFAULT_SENDER=votre-email@gmail.com

# Configuration de la base de données PostgreSQL
DATABASE_URL=postgresql://notation_user:VOTRE_MOT_DE_PASSE_SECURISE@localhost/notation_app

# Configuration du serveur
FLASK_ENV=production
FLASK_DEBUG=False

# Configuration du domaine (remplacez par votre domaine ou sous-domaine)
DOMAIN=app.votre-domaine.com
APP_URL=https://app.votre-domaine.com
```

**Note** : Si vous utilisez un sous-domaine, remplacez `app.votre-domaine.com` par votre sous-domaine réel (ex: `notation.votre-domaine.com`, `admin.votre-domaine.com`, etc.)

````

**⚠️ Important** :
- Générez une `SECRET_KEY` sécurisée avec : `python3 -c "import secrets; print(secrets.token_hex(32))"`
- Utilisez le **mot de passe d'application Gmail** (pas votre mot de passe Gmail normal)
- Remplacez `VOTRE_MOT_DE_PASSE_SECURISE` par le mot de passe PostgreSQL créé à l'étape 4

### 6.3 Initialisation de la base de données

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Définir l'application Flask
export FLASK_APP=run.py

# Initialiser la base de données
flask init-db

# Créer un administrateur
flask create-admin
# Suivez les instructions pour créer votre compte admin
````

---

## Étape 7 : Configuration de Gunicorn et Supervisor

### 7.1 Création du fichier de configuration Supervisor

```bash
cd /var/www/Projet-notation

# Copier la configuration
cp deploy/supervisor.conf /etc/supervisor/conf.d/notation-app.conf

# Vérifier que le fichier est correct
cat /etc/supervisor/conf.d/notation-app.conf
```

### 7.2 Ajuster la configuration si nécessaire

```bash
nano /etc/supervisor/conf.d/notation-app.conf
```

Vérifiez que le chemin est correct : `/var/www/Projet-notation`

### 7.3 Démarrer l'application avec Supervisor

```bash
# Recharger la configuration
supervisorctl reread
supervisorctl update

# Démarrer l'application
supervisorctl start notation-app

# Vérifier le statut
supervisorctl status
```

Vous devriez voir : `notation-app RUNNING pid XXXX`

### 7.4 Vérifier les logs

```bash
# Voir les logs en temps réel
tail -f /var/log/notation-app.log

# Tester que l'application répond
curl http://localhost:8000
```

---

## Étape 8 : Configuration de Nginx

### 8.1 Création de la configuration Nginx

```bash
cd /var/www/Projet-notation

# Choisir la configuration selon votre choix :
# - Pour un domaine principal : utilisez nginx.conf
# - Pour un sous-domaine : utilisez nginx.conf.sous-domaine.example

# Option A : Domaine principal
cp deploy/nginx.conf /etc/nginx/sites-available/notation-app

# Option B : Sous-domaine (recommandé)
cp deploy/nginx.conf.sous-domaine.example /etc/nginx/sites-available/notation-app

# Éditer pour mettre votre domaine ou sous-domaine
nano /etc/nginx/sites-available/notation-app
```

### 8.2 Modifier le domaine dans nginx.conf

Remplacez `votre-domaine.com` par votre vrai domaine dans le fichier.

**Pour un domaine principal** :

```nginx
server_name votre-domaine.com www.votre-domaine.com;
```

**Pour un sous-domaine** (exemple avec `app.votre-domaine.com`) :

```nginx
server_name app.votre-domaine.com;
```

**Exemple complet avec sous-domaine** :

```nginx
server {
    listen 80;
    server_name app.votre-domaine.com;  # Votre sous-domaine

    # ... reste de la configuration ...
}
```

### 8.3 Activer le site

```bash
# Créer le lien symbolique
ln -s /etc/nginx/sites-available/notation-app /etc/nginx/sites-enabled/

# Supprimer la configuration par défaut
rm /etc/nginx/sites-enabled/default

# Tester la configuration
nginx -t

# Si tout est OK, redémarrer Nginx
systemctl restart nginx
```

### 8.4 Vérifier que Nginx fonctionne

```bash
# Vérifier le statut
systemctl status nginx

# Voir les logs
tail -f /var/log/nginx/notation-app.error.log
```

---

## Étape 9 : Configuration SSL/HTTPS

### 9.1 Installation de Certbot

```bash
# Installer Certbot
apt install certbot python3-certbot-nginx -y
```

### 9.2 Configuration DNS

**Avant de continuer**, assurez-vous que votre domaine pointe vers l'IP du serveur.

#### Option A : Utiliser le domaine principal

1. Allez dans votre **panneau de gestion DNS** (chez Ionos ou votre registrar)
2. Créez un enregistrement **A** :
   - **Nom** : `@` (ou votre domaine)
   - **Valeur** : L'IP de votre serveur VPS
3. Créez un enregistrement **A** pour `www` :
   - **Nom** : `www`
   - **Valeur** : L'IP de votre serveur VPS
4. Attendez la propagation DNS (5-30 minutes)

#### Option B : Utiliser un sous-domaine (Recommandé) ✅

**Avantages d'un sous-domaine** :

- ✅ Séparation claire entre votre site principal et l'application
- ✅ Plus facile à gérer et à mémoriser
- ✅ Permet d'héberger plusieurs applications sur le même serveur
- ✅ Exemples : `app.votre-domaine.com`, `notation.votre-domaine.com`, `admin.votre-domaine.com`

**Configuration DNS pour un sous-domaine** :

1. Allez dans votre **panneau de gestion DNS** (chez Ionos ou votre registrar)
2. Créez un enregistrement **A** pour votre sous-domaine :
   - **Nom** : `app` (ou `notation`, `admin`, etc.)
   - **Valeur** : L'IP de votre serveur VPS
   - **Résultat** : `app.votre-domaine.com` pointera vers votre serveur
3. Attendez la propagation DNS (5-30 minutes)

**Exemples de sous-domaines courants** :

- `app.votre-domaine.com` - Application principale
- `notation.votre-domaine.com` - Application de notation
- `admin.votre-domaine.com` - Interface d'administration
- `api.votre-domaine.com` - API (si vous en avez une)

### 9.3 Vérification DNS

**Pour un domaine principal** :

```bash
# Vérifier que le DNS est correct
nslookup votre-domaine.com
# Doit afficher l'IP de votre serveur
```

**Pour un sous-domaine** :

```bash
# Vérifier que le DNS est correct
nslookup app.votre-domaine.com
# Doit afficher l'IP de votre serveur
```

**Alternative avec dig** :

```bash
# Plus détaillé
dig app.votre-domaine.com +short
# Doit retourner l'IP de votre serveur
```

### 9.4 Obtenir le certificat SSL

**Pour un domaine principal** :

```bash
# Obtenir le certificat SSL
certbot --nginx -d votre-domaine.com -d www.votre-domaine.com
```

**Pour un sous-domaine** (exemple avec `app.votre-domaine.com`) :

```bash
# Obtenir le certificat SSL pour le sous-domaine uniquement
certbot --nginx -d app.votre-domaine.com
```

**Suivez les instructions** :

- Entrez votre email
- Acceptez les conditions
- Choisissez de rediriger HTTP vers HTTPS (option 2)

**Note** : Si vous utilisez un sous-domaine, vous n'avez pas besoin de configurer le domaine principal. Le certificat SSL fonctionnera uniquement pour le sous-domaine.

### 9.5 Renouvellement automatique

Certbot configure automatiquement le renouvellement. Vérifiez avec :

```bash
# Tester le renouvellement
certbot renew --dry-run
```

---

## Étape 10 : Configuration du firewall

### 10.1 Configuration UFW

```bash
# Autoriser SSH (IMPORTANT : faites-le en premier !)
ufw allow 22/tcp

# Autoriser HTTP et HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Activer le firewall
ufw enable

# Vérifier le statut
ufw status
```

**⚠️ Attention** : Ne fermez jamais le port 22 avant d'avoir testé que tout fonctionne !

---

## Vérification et tests

### Test 1 : Application locale

```bash
# Sur le serveur
curl http://localhost:8000
# Doit retourner du HTML
```

### Test 2 : Application via Nginx

```bash
# Sur le serveur
curl http://localhost
# Doit retourner du HTML
```

### Test 3 : Depuis votre navigateur

1. Ouvrez votre navigateur
2. Allez sur `http://VOTRE_IP` ou `https://votre-domaine.com`
3. Vous devriez voir la page de connexion de l'application

### Test 4 : Connexion admin

1. Connectez-vous avec le compte admin créé à l'étape 6.3
2. Vérifiez que le dashboard fonctionne

### Commandes de vérification

```bash
# Statut de l'application
supervisorctl status notation-app

# Statut de Nginx
systemctl status nginx

# Statut de PostgreSQL
systemctl status postgresql

# Logs de l'application
tail -f /var/log/notation-app.log

# Logs Nginx
tail -f /var/log/nginx/notation-app.error.log
```

---

## Mise à jour de l'application

### Workflow de mise à jour

Le processus de mise à jour se fait en **2 étapes** :

1. **Sur votre machine locale** : Pousser les changements sur GitHub
2. **Sur le serveur de production** : Récupérer et déployer les changements

### Étape 1 : Pousser les changements sur GitHub (Machine locale)

Depuis votre machine de développement :

```bash
# Aller dans le dossier du projet
cd "C:\Users\Antoine\Documents\Projet notation"

# Vérifier les changements
git status

# Ajouter tous les fichiers modifiés
git add -A

# Créer un commit
git commit -m "Description des changements"

# Pousser vers GitHub
git push origin main
```

**⚠️ Important** : Assurez-vous que tous vos changements sont bien commités et poussés sur GitHub avant de continuer.

### Étape 2 : Déployer sur le serveur de production

Une fois les changements sur GitHub, connectez-vous au serveur :

```bash
# Se connecter au serveur
ssh root@VOTRE_IP_SERVEUR

# Aller dans le dossier de l'application
cd /var/www/Projet-notation

# Activer l'environnement virtuel
source venv/bin/activate

# Récupérer les dernières modifications depuis GitHub
git pull origin main

# Mettre à jour les dépendances Python (si requirements.txt a changé)
pip install -r requirements.txt

# Appliquer les migrations de base de données (si nécessaire)
export FLASK_APP=run.py
flask db upgrade

# Redémarrer l'application pour appliquer les changements
supervisorctl restart notation-app

# Vérifier que tout fonctionne
supervisorctl status notation-app
tail -f /var/log/notation-app.log
```

### Résumé du workflow

```
Machine locale          GitHub              Serveur production
     |                    |                        |
     |-- git push ------>|                        |
     |                    |                        |
     |                    |<-- git pull ----------|
     |                    |                        |
     |                    |              [Redémarrage app]
```

### Cas particuliers

#### Si vous avez modifié le fichier .env

Le fichier `.env` n'est **pas** versionné sur GitHub (pour des raisons de sécurité). Si vous devez modifier des variables d'environnement (ex. nouveau compte Gmail) :

```bash
# Sur le serveur
cd /var/www/Projet-notation
nano .env
# Modifier les variables nécessaires (MAIL_USERNAME, MAIL_PASSWORD, MAIL_DEFAULT_SENDER, etc.)
# Sauvegarder (Ctrl+O, Entrée) puis quitter (Ctrl+X)
# Redémarrer l'application pour appliquer les changements
supervisorctl restart notation-app
```

**Guide détaillé** : voir **[MISE_A_JOUR_ENV_PRODUCTION.md](MISE_A_JOUR_ENV_PRODUCTION.md)**.

#### Si vous avez ajouté de nouvelles dépendances

Si vous avez ajouté de nouveaux packages dans `requirements.txt` :

```bash
# Sur le serveur, après git pull
source venv/bin/activate
pip install -r requirements.txt
supervisorctl restart notation-app
```

#### Si vous avez modifié la structure de la base de données

Si vous avez créé de nouvelles migrations :

```bash
# Sur le serveur, après git pull
source venv/bin/activate
export FLASK_APP=run.py
flask db upgrade
supervisorctl restart notation-app
```

---

## Dépannage

### Problème 1 : L'application ne démarre pas

```bash
# Vérifier le statut
supervisorctl status notation-app

# Voir les logs
tail -50 /var/log/notation-app.log

# Redémarrer
supervisorctl restart notation-app
```

**Causes courantes** :

- Erreur dans le fichier `.env`
- Problème de connexion à la base de données
- Port 8000 déjà utilisé

### Problème 2 : Erreur 502 Bad Gateway

```bash
# Vérifier que l'application tourne
supervisorctl status notation-app

# Vérifier que Gunicorn écoute sur le port 8000
netstat -tlnp | grep 8000

# Vérifier les logs Nginx
tail -f /var/log/nginx/notation-app.error.log
```

### Problème 3 : Erreur de base de données

```bash
# Se connecter à PostgreSQL
sudo -u postgres psql -d notation_app

# Vérifier les tables
\dt

# Vérifier les utilisateurs
\du
```

### Problème 4 : Certificat SSL ne fonctionne pas

```bash
# Vérifier le certificat
certbot certificates

# Renouveler manuellement
certbot renew

# Vérifier la configuration Nginx
nginx -t
```

### Problème 5 : Email ne fonctionne pas

1. Vérifiez que vous utilisez un **mot de passe d'application Gmail** (pas votre mot de passe normal)
2. Vérifiez les variables dans `.env`
3. Testez avec le script : `python scripts/test_email_config.py`

### Commandes utiles

```bash
# Redémarrer tous les services
supervisorctl restart notation-app
systemctl restart nginx
systemctl restart postgresql

# Voir tous les logs
journalctl -xe

# Vérifier l'espace disque
df -h

# Vérifier la mémoire
free -h

# Vérifier les processus
ps aux | grep gunicorn
```

---

## Checklist finale

Avant de considérer le déploiement terminé, vérifiez :

- [ ] VPS Ionos acheté et configuré
- [ ] Serveur accessible via SSH
- [ ] Toutes les dépendances installées
- [ ] PostgreSQL configuré et base de données créée
- [ ] Application clonée et dépendances Python installées
- [ ] Fichier `.env` configuré avec toutes les variables
- [ ] Base de données initialisée (`flask init-db`)
- [ ] Compte administrateur créé
- [ ] Gunicorn configuré avec Supervisor
- [ ] Application accessible sur `http://localhost:8000`
- [ ] Nginx configuré et fonctionnel
- [ ] Application accessible via IP ou domaine
- [ ] SSL/HTTPS configuré (si domaine disponible)
- [ ] Firewall configuré (ports 22, 80, 443)
- [ ] Application testée dans le navigateur
- [ ] Connexion admin fonctionnelle
- [ ] Logs vérifiés (pas d'erreurs)

---

## Sauvegarde de la base de données

Pour ne pas perdre les données en cas de problème, sauvegardez régulièrement la base PostgreSQL et récupérez les dumps sur votre PC.

**Sur le VPS** (créer un dump) :

```bash
cd /var/www/Projet-notation
./deploy/backup_db.sh
```

Le fichier est créé dans `backups/db_AAAA-MM-JJ_HH-MM.dump`.

**Depuis votre PC** (récupérer les sauvegardes) :

```powershell
scp -r root@VOTRE_IP:/var/www/Projet-notation/backups ./backups-vps
```

**Procédure complète** (sauvegarde, récupération, restauration, cron) : voir **[SAUVEGARDE_VPS.md](SAUVEGARDE_VPS.md)**.

---

## Support et ressources

- **Documentation Ionos** : https://www.ionos.fr/assistance/serveurs/vps
- **Documentation Nginx** : https://nginx.org/en/docs/
- **Documentation Gunicorn** : https://docs.gunicorn.org/
- **Documentation Supervisor** : http://supervisord.org/

---

## Coûts estimés

- **VPS Ionos S** : ~5€/mois
- **Domaine** : ~10-15€/an (optionnel)
- **Total** : ~5-6€/mois

---

**Félicitations !** 🎉 Votre application est maintenant en production et accessible 24h/24 !
