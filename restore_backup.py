import os
import shutil

EXCLUDES = {'.git', 'venv', '__pycache__', 'backups', '.gitignore', '.flaskenv'}
BACKUP_DIR = 'backups'


def list_backups():
    if not os.path.exists(BACKUP_DIR):
        print("Aucun dossier de backup trouvé.")
        return []
    backups = [d for d in os.listdir(BACKUP_DIR) if os.path.isdir(os.path.join(BACKUP_DIR, d))]
    backups.sort()
    return backups


def should_exclude(name):
    return name in EXCLUDES


def copytree(src, dst):
    for item in os.listdir(src):
        if should_exclude(item):
            continue
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            if os.path.exists(d):
                shutil.rmtree(d)
            shutil.copytree(s, d, ignore=shutil.ignore_patterns(*EXCLUDES))
        else:
            shutil.copy2(s, d)


def main():
    backups = list_backups()
    if not backups:
        return
    print("Backups disponibles :")
    for b in backups:
        print(f"- {b}")
    backup_name = input("Nom du backup à restaurer : ").strip()
    if backup_name not in backups:
        print("Backup non trouvé.")
        return
    confirm = input(f"Cette opération va écraser le code actuel par '{backup_name}'. Continuer ? (o/n) : ").lower()
    if confirm != 'o':
        print("Opération annulée.")
        return
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    print(f"Restauration du backup '{backup_name}'...")
    copytree(backup_path, '.')
    print("Restauration terminée !")


if __name__ == '__main__':
    main() 