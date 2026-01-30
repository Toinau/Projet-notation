# Sauvegarde et récupération – VPS (base de données)

Ce guide explique comment **sauvegarder la base PostgreSQL** sur le VPS et **récupérer les sauvegardes** sur votre machine pour ne pas perdre les données en cas de problème.

---

## 1. Sauvegarder la base sur le VPS

### Option A : Script fourni (recommandé)

Sur le serveur, à la racine du projet :

```bash
ssh root@VOTRE_IP_SERVEUR
cd /var/www/Projet-notation
chmod +x deploy/backup_db.sh
./deploy/backup_db.sh
```

Le script lit `DATABASE_URL` dans le fichier `.env`, crée un dump PostgreSQL et l’enregistre dans `backups/` avec la date (ex. `backups/db_2026-01-30_14-30.dump`).

### Option B : Commande manuelle

```bash
cd /var/www/Projet-notation
mkdir -p backups

# Récupérer l’URL depuis .env (sans guillemets)
source .env 2>/dev/null || true
# Si .env n’exporte pas les variables, utilisez :
# export $(grep -E '^DATABASE_URL=' .env | xargs)

# Dump au format personnalisé (recommandé pour restauration)
pg_dump "$DATABASE_URL" -F c -f backups/db_$(date +%Y-%m-%d_%H-%M).dump
```

Ou en indiquant utilisateur, base et mot de passe :

```bash
pg_dump -U notation_user -h localhost -d notation_app -F c -f backups/db_$(date +%Y-%m-%d_%H-%M).dump
# Mot de passe demandé = celui de l’utilisateur PostgreSQL (dans .env, dans DATABASE_URL)
```

---

## 2. Récupérer les sauvegardes sur votre PC

Une fois le dump créé sur le VPS, **téléchargez-le** sur votre machine pour en garder une copie locale.

### Avec SCP (depuis votre machine Windows / PowerShell)

```powershell
# Un seul fichier (remplacer par le nom réel du dump)
scp root@VOTRE_IP_SERVEUR:/var/www/Projet-notation/backups/db_2026-01-30_14-30.dump .

# Tous les dumps du dossier backups
scp -r root@VOTRE_IP_SERVEUR:/var/www/Projet-notation/backups ./backups-vps
```

### Avec SCP (depuis Linux / Mac)

```bash
scp root@VOTRE_IP_SERVEUR:/var/www/Projet-notation/backups/db_*.dump ./
# ou tout le dossier
scp -r root@VOTRE_IP_SERVEUR:/var/www/Projet-notation/backups ./backups-vps
```

Conseil : créer un dossier local dédié (ex. `backups-vps/`) et y copier régulièrement les dumps pour ne pas perdre la base en cas de panne du VPS.

---

## 3. Restaurer la base (en cas de problème)

### Sur le VPS (après incident)

```bash
cd /var/www/Projet-notation

# Arrêter l’application pour éviter les écritures pendant la restauration
supervisorctl stop notation-app

# Restaurer depuis un dump (remplacer par votre fichier .dump)
pg_restore -U notation_user -h localhost -d notation_app --clean --if-exists backups/db_2026-01-30_14-30.dump
# ou avec l’URL :
pg_restore "$DATABASE_URL" --clean --if-exists backups/db_2026-01-30_14-30.dump

# Redémarrer l’application
supervisorctl start notation-app
```

Si la base est entièrement détruite, la recréer puis restaurer :

```bash
sudo -u postgres psql -c "DROP DATABASE IF EXISTS notation_app;"
sudo -u postgres psql -c "CREATE DATABASE notation_app;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE notation_app TO notation_user;"
pg_restore -U notation_user -h localhost -d notation_app backups/db_XXXX.dump
```

### À partir d’une sauvegarde récupérée sur votre PC

1. Copier le fichier `.dump` sur le VPS :
   ```bash
   scp ./db_2026-01-30.dump root@VOTRE_IP:/var/www/Projet-notation/backups/
   ```
2. Puis sur le VPS, exécuter les commandes de restauration ci-dessus.

---

## 4. Automatiser les sauvegardes (cron)

Pour des sauvegardes régulières sans y penser, ajoutez une tâche cron **sur le VPS** :

```bash
crontab -e
```

Exemple : sauvegarde tous les jours à 3 h du matin :

```
0 3 * * * cd /var/www/Projet-notation && ./deploy/backup_db.sh
```

Pour ne garder que les N derniers dumps (éviter de remplir le disque), vous pouvez ajouter dans `backup_db.sh` une suppression des anciens fichiers (ex. garder les 7 derniers). Voir le script pour une option possible.

---

## 5. Récapitulatif

| Action | Où | Commande |
|--------|-----|----------|
| Créer un dump | Sur le VPS | `./deploy/backup_db.sh` ou `pg_dump ...` |
| Télécharger le dump | Depuis votre PC | `scp root@IP:/var/www/Projet-notation/backups/db_*.dump .` |
| Restaurer | Sur le VPS | `pg_restore ... backups/db_XXX.dump` |

En sauvegardant régulièrement et en téléchargeant les dumps sur votre machine (ou un autre stockage), vous limitez le risque de perdre la base de données en cas de problème sur le VPS.
