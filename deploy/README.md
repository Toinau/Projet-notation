# Déploiement

Fichiers pour déployer l’application sur un VPS (Nginx, Gunicorn, Supervisor).

- **deploy.sh** – Script de déploiement automatique (à lancer depuis la racine : `./deploy/deploy.sh IP_SERVEUR`)
- **production.env.example** – Modèle de `.env` pour la production
- **supervisor.conf** – Configuration Supervisor (Gunicorn)
- **nginx.conf** / **nginx.conf.sous-domaine.example** – Configurations Nginx

Voir `docs/GUIDE_DEPLOIEMENT_IONOS.md` pour les étapes détaillées.
