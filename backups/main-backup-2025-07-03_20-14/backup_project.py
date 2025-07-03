import os
import shutil
from datetime import datetime

# Dossiers/fichiers à exclure du backup
EXCLUDES = {'.git', 'venv', '__pycache__', 'backups', '.gitignore', '.flaskenv'}

# Dossier de destination des backups
BACKUP_DIR = 'backups'


def should_exclude(name):
    return name in EXCLUDES


def copytree(src, dst):
    os.makedirs(dst, exist_ok=True)
    for item in os.listdir(src):
        if should_exclude(item):
            continue
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, ignore=shutil.ignore_patterns(*EXCLUDES))
        else:
            shutil.copy2(s, d)


def main():
    # Créer le dossier backups s'il n'existe pas
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    # Nom du sous-dossier de backup avec date et heure
    now = datetime.now().strftime('%Y-%m-%d_%H-%M')
    backup_name = f"main-backup-{now}"
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    # Copier le projet
    print(f"Sauvegarde du projet dans : {backup_path}")
    copytree('.', backup_path)
    print("Backup terminé !")


if __name__ == '__main__':
    main() 