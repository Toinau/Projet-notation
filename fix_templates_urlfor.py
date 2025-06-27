import os
import re

TEMPLATES_DIR = "templates"

def fix_url_for_in_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Remplace url_for('quelquechose') par url_for('main.quelquechose') si ce n'est pas déjà préfixé
    new_content = re.sub(
        r"url_for\('([a-zA-Z0-9_]+)'",
        lambda m: f"url_for('main.{m.group(1)}'" if not m.group(1).startswith("main.") else m.group(0),
        content
    )

    if new_content != content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Corrigé : {filepath}")

def walk_templates_and_fix():
    for root, dirs, files in os.walk(TEMPLATES_DIR):
        for file in files:
            if file.endswith(".html"):
                fix_url_for_in_file(os.path.join(root, file))

if __name__ == "__main__":
    walk_templates_and_fix()
    print("✅ Correction automatique terminée !") 