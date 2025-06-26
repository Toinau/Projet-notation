import os
import subprocess
from datetime import datetime

# === Configuration ===
REPO_URL = "https://github.com/Toinau/Projet-notation.git"  
BRANCH = "main"  # ou "master"
COMMIT_MESSAGE = f"Backup auto - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

def run_git_command(command):
    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    if result.returncode != 0:
        print(f"Erreur avec la commande : {command}")
        print(result.stderr)
    else:
        print(result.stdout)

def git_backup():
    # Initialiser git si nécessaire
    if not os.path.isdir(".git"):
        print("Initialisation du dépôt Git...")
        run_git_command("git init")
        run_git_command(f"git remote add origin {REPO_URL}")
        run_git_command(f"git branch -M {BRANCH}")

    # Ajouter les fichiers
    print("Ajout des fichiers au suivi Git...")
    run_git_command("git add .")

    # Commit
    print("Création du commit...")
    run_git_command(f'git commit -m "{COMMIT_MESSAGE}"')

    # Push vers GitHub
    print("Envoi vers GitHub...")
    run_git_command(f"git push origin {BRANCH}")

    print("✅ Backup terminé avec succès.")

if __name__ == "__main__":
    git_backup()
