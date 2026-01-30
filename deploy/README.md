# Déploiement

Fichiers pour déployer l’application sur un VPS (Nginx, Gunicorn, Supervisor).

- **deploy.sh** – Script de déploiement automatique (à lancer depuis la racine : `./deploy/deploy.sh IP_SERVEUR`)
- **backup_db.sh** – Sauvegarde de la base PostgreSQL sur le VPS (à lancer depuis la racine : `./deploy/backup_db.sh`)
- **production.env.example** – Modèle de `.env` pour la production
- **supervisor.conf** – Configuration Supervisor (Gunicorn)
- **nginx.conf** / **nginx.conf.sous-domaine.example** – Configurations Nginx

Voir `docs/GUIDE_DEPLOIEMENT_IONOS.md` pour les étapes détaillées et `docs/SAUVEGARDE_VPS.md` pour la sauvegarde de la base de données.
