import subprocess
from datetime import datetime

# === Configuration ===
BRANCH = "main"
COMMIT_MESSAGE = f"Push automatique - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

def run(command):
    result = subprocess.run(command, shell=True, text=True)
    if result.returncode != 0:
        print(f"❌ Erreur : {command}")
    else:
        print(f"✅ Commande exécutée : {command}")

# === Étapes Git ===
print("📁 Ajout des fichiers...")
run("git add .")

print("📝 Commit des changements...")
run(f'git commit -m "{COMMIT_MESSAGE}"')

print(f"🚀 Push vers la branche {BRANCH}...")
run(f"git push origin {BRANCH}")
