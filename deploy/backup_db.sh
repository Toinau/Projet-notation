#!/bin/bash
# Sauvegarde de la base PostgreSQL (à exécuter sur le VPS, à la racine du projet)
# Usage: cd /var/www/Projet-notation && ./deploy/backup_db.sh

set -e

# Aller à la racine du projet (parent du dossier deploy/)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

BACKUP_DIR="backups"
mkdir -p "$BACKUP_DIR"

# Lire DATABASE_URL depuis .env (ligne DATABASE_URL=... sans guillemets)
if [ ! -f .env ]; then
    echo "Erreur: fichier .env introuvable dans $PROJECT_ROOT"
    exit 1
fi

DATABASE_URL=$(grep -E '^DATABASE_URL=' .env | cut -d= -f2- | tr -d '"' | tr -d "'" | head -1)
if [ -z "$DATABASE_URL" ]; then
    echo "Erreur: DATABASE_URL non trouvé dans .env"
    exit 1
fi

# Nom du fichier avec date/heure
BACKUP_FILE="$BACKUP_DIR/db_$(date +%Y-%m-%d_%H-%M).dump"

echo "Sauvegarde de la base dans $BACKUP_FILE ..."
pg_dump "$DATABASE_URL" -F c -f "$BACKUP_FILE"

echo "Sauvegarde terminée: $BACKUP_FILE"
echo "Pour récupérer sur votre PC: scp root@IP_SERVEUR:$PROJECT_ROOT/$BACKUP_FILE ."

# Optionnel: garder seulement les 10 derniers dumps (décommenter si besoin)
# ls -t "$BACKUP_DIR"/db_*.dump 2>/dev/null | tail -n +11 | xargs -r rm --
# echo "Anciens dumps supprimés (10 derniers conservés)."
