# 🚀 Guide de Déploiement en Production - VPS Ionos

## 📋 Prérequis

### 1. Achat du VPS Ionos
- **Allez sur** : https://www.ionos.fr/serveurs/vps
- **Choisissez** : VPS S (2 vCPU, 4 GB RAM, 80 GB SSD)
- **Système** : Ubuntu 22.04 LTS
- **Prix** : ~5€/mois

### 2. Informations nécessaires
Après l'achat, vous recevrez :
- **Adresse IP** du serveur
- **Nom d'utilisateur** : `root`
- **Mot de passe** temporaire

## 🔧 Étapes de Déploiement

### Étape 1 : Connexion au serveur
```bash
ssh root@VOTRE_IP_SERVEUR
```

### Étape 2 : Déploiement automatique
```bash
# Depuis votre machine locale (à la racine du projet)
chmod +x deploy/deploy.sh
./deploy/deploy.sh VOTRE_IP_SERVEUR
```

### Étape 3 : Configuration manuelle
```bash
# Se connecter au serveur
ssh root@VOTRE_IP_SERVEUR

# Aller dans le dossier de l'application
cd /var/www/Projet-notation

# Créer le fichier .env
cp deploy/production.env.example .env
nano .env
```

### Étape 4 : Configuration du fichier .env
```env
SECRET_KEY=votre-clé-secrète-très-sécurisée-changez-moi-en-production
MAIL_USERNAME=votre-email@gmail.com
MAIL_PASSWORD=votre-mot-de-passe-app-gmail
MAIL_DEFAULT_SENDER=votre-email@gmail.com
DATABASE_URL=postgresql://notation_user:notation_password_2024@localhost/notation_app
FLASK_ENV=production
FLASK_DEBUG=False
DOMAIN=votre-domaine.com
```

### Étape 5 : Initialisation de l'application
```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Initialiser la base de données
export FLASK_APP=run.py
flask init-db

# Créer un administrateur
flask create-admin
```

### Étape 6 : Configuration de Nginx
```bash
# Copier la configuration Nginx
cp deploy/nginx.conf /etc/nginx/sites-available/notation-app

# Modifier le domaine dans le fichier
nano /etc/nginx/sites-available/notation-app
# Remplacer "votre-domaine.com" par votre vrai domaine

# Activer le site
ln -s /etc/nginx/sites-available/notation-app /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default  # Supprimer la page par défaut

# Tester la configuration
nginx -t

# Redémarrer Nginx
systemctl restart nginx
```

### Étape 7 : Configuration de Supervisor
```bash
# Copier la configuration Supervisor
cp deploy/supervisor.conf /etc/supervisor/conf.d/notation-app.conf

# Redémarrer Supervisor
supervisorctl reread
supervisorctl update
supervisorctl start notation-app
```

### Étape 8 : Configuration du firewall
```bash
# Installer UFW
apt install ufw

# Configurer le firewall
ufw allow 22    # SSH
ufw allow 80    # HTTP
ufw allow 443   # HTTPS
ufw enable
```

### Étape 9 : Configuration SSL (optionnel)
```bash
# Installer Certbot
apt install certbot python3-certbot-nginx

# Obtenir le certificat SSL
certbot --nginx -d votre-domaine.com -d www.votre-domaine.com
```

## 🔍 Vérification

### Tester l'application
```bash
# Vérifier que l'application fonctionne
curl http://localhost:8000

# Vérifier les logs
tail -f /var/log/notation-app.log
tail -f /var/log/nginx/notation-app.error.log
```

### Commandes utiles
```bash
# Redémarrer l'application
supervisorctl restart notation-app

# Voir le statut
supervisorctl status

# Redémarrer Nginx
systemctl restart nginx

# Voir les logs en temps réel
tail -f /var/log/notation-app.log
```

## 🔄 Mise à jour de l'application

```bash
# Se connecter au serveur
ssh root@VOTRE_IP_SERVEUR

# Aller dans le dossier
cd /var/www/Projet-notation

# Mettre à jour le code
git pull origin main

# Mettre à jour les dépendances
source venv/bin/activate
pip install -r requirements.txt

# Redémarrer l'application
supervisorctl restart notation-app
```

## 🛠️ Dépannage

### Problèmes courants

1. **Application ne démarre pas**
   ```bash
   supervisorctl status
   tail -f /var/log/notation-app.log
   ```

2. **Erreur de base de données**
   ```bash
   sudo -u postgres psql -d notation_app
   ```

3. **Erreur Nginx**
   ```bash
   nginx -t
   tail -f /var/log/nginx/error.log
   ```

## 📞 Support

En cas de problème :
1. Vérifiez les logs : `/var/log/notation-app.log`
2. Vérifiez le statut : `supervisorctl status`
3. Redémarrez : `supervisorctl restart notation-app`

## ✅ Checklist de Production

- [ ] VPS Ionos acheté et configuré
- [ ] Déploiement automatique effectué
- [ ] Fichier .env configuré
- [ ] Base de données initialisée
- [ ] Administrateur créé
- [ ] Nginx configuré
- [ ] Supervisor configuré
- [ ] Firewall activé
- [ ] SSL configuré (optionnel)
- [ ] Application testée
- [ ] Logs vérifiés 