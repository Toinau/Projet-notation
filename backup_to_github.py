import os
import shutil
import subprocess
from datetime import datetime

# === CONFIGURATION ===
GITHUB_BACKUP_REPO = "https://github.com/Toinau/projet-notation-back-up.git"  
BRANCH = "main"

# === Création du dossier de backup ===
timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
backup_dir = f"backups/main-backup-{timestamp}"

print(f"🗂️ Création du dossier de backup : {backup_dir}")
os.makedirs(backup_dir, exist_ok=True)

# === Fichiers à exclure ===
excluded = {'__pycache__', '.git', 'backups', '.venv', 'node_modules'}

def should_copy(path):
    return not any(part in excluded for part in path.split(os.sep))

# === Copier les fichiers ===
for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if should_copy(os.path.join(root, d))]
    if should_copy(root):
        for file in files:
            src_path = os.path.join(root, file)
            if should_copy(src_path) and os.path.isfile(src_path):
                dst_path = os.path.join(backup_dir, os.path.relpath(src_path, "."))
                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                shutil.copy2(src_path, dst_path)

# === Initialiser Git dans le dossier backup ===
print("🚀 Initialisation du dépôt Git dans le dossier de backup")
os.chdir(backup_dir)
subprocess.run(["git", "init"])
subprocess.run(["git", "branch", "-M", BRANCH])
subprocess.run(["git", "remote", "add", "origin", GITHUB_BACKUP_REPO])
subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", f"Backup du {timestamp}"])
# Forcer le push
subprocess.run(["git", "push", "-f", "origin", BRANCH])

print("✅ Backup complet envoyé sur GitHub (push forcé).")
