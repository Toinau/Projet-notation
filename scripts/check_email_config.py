#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour vérifier la configuration email actuelle de l'application
"""

import os
import sys
import io

# Forcer l'encodage UTF-8 pour Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from dotenv import load_dotenv

# Charger le fichier .env
load_dotenv()

print("=" * 60)
print("VÉRIFICATION DE LA CONFIGURATION EMAIL")
print("=" * 60)
print()

# Vérifier si le fichier .env existe
env_path = '.env'
if not os.path.exists(env_path):
    print(f"❌ Fichier .env NON TROUVÉ à : {os.path.abspath(env_path)}")
    print("   Créez un fichier .env à la racine du projet")
    sys.exit(1)

print(f"✅ Fichier .env trouvé : {os.path.abspath(env_path)}")
print()

# Lire le contenu du fichier .env (pour vérifier le format)
print("📄 Contenu du fichier .env (variables email uniquement) :")
print("-" * 60)

with open(env_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    mail_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#') and any(var in stripped for var in ['MAIL_', 'mail_']):
            mail_lines.append(line.rstrip())
    
    if mail_lines:
        for line in mail_lines:
            # Masquer le mot de passe
            if 'MAIL_PASSWORD=' in line or 'mail_password=' in line:
                parts = line.split('=', 1)
                if len(parts) == 2:
                    password = parts[1]
                    masked = parts[0] + '=' + ('*' * min(len(password), 20))
                    if len(password) > 20:
                        masked += f" ({len(password)} caractères)"
                    print(f"  {masked}")
                else:
                    print(f"  {line}")
            else:
                print(f"  {line}")
    else:
        print("  ❌ Aucune variable MAIL_ trouvée dans le fichier .env")

print()

# Vérifier les variables d'environnement chargées
print("🔍 Variables d'environnement chargées :")
print("-" * 60)

mail_vars = {
    'MAIL_SERVER': os.environ.get('MAIL_SERVER'),
    'MAIL_PORT': os.environ.get('MAIL_PORT'),
    'MAIL_USE_TLS': os.environ.get('MAIL_USE_TLS'),
    'MAIL_USERNAME': os.environ.get('MAIL_USERNAME'),
    'MAIL_PASSWORD': os.environ.get('MAIL_PASSWORD'),
    'MAIL_DEFAULT_SENDER': os.environ.get('MAIL_DEFAULT_SENDER'),
}

all_ok = True
issues = []

for var_name, var_value in mail_vars.items():
    if var_value:
        if var_name == 'MAIL_PASSWORD':
            masked = '*' * min(len(var_value), 20)
            if len(var_value) > 20:
                masked += f" ({len(var_value)} caractères)"
            else:
                masked += f" ({len(var_value)} caractères)"
            print(f"  ✅ {var_name}: {masked}")
            
            # Vérifications spécifiques pour le mot de passe
            if ' ' in var_value:
                issues.append(f"⚠️  Le mot de passe contient des espaces (supprimez-les)")
                all_ok = False
            
            if len(var_value) != 16:
                issues.append(f"⚠️  Le mot de passe fait {len(var_value)} caractères (devrait être 16 pour un mot de passe d'application Gmail)")
        else:
            print(f"  ✅ {var_name}: {var_value}")
    else:
        print(f"  ❌ {var_name}: NON DÉFINI")
        all_ok = False
        issues.append(f"Variable {var_name} manquante")

print()

if issues:
    print("⚠️  PROBLÈMES DÉTECTÉS :")
    print("-" * 60)
    for issue in issues:
        print(f"  {issue}")
    print()

if not all_ok:
    print("💡 SOLUTIONS :")
    print("-" * 60)
    print("  1. Vérifiez que toutes les variables sont définies dans le fichier .env")
    print("  2. Utilisez un mot de passe d'application Gmail (16 caractères, SANS espaces)")
    print("  3. Pour créer un mot de passe d'application :")
    print("     https://myaccount.google.com/apppasswords")
    print("  4. Après modification du .env, REDÉMARREZ votre application Flask")
    print("  5. Exécutez : python configure_gmail.py")
    print()
    print("   Pour tester la configuration : python test_email_config.py")
else:
    print("✅ Configuration correcte !")
    print()
    print("💡 Si l'email ne fonctionne toujours pas :")
    print("   1. Assurez-vous d'avoir REDÉMARRÉ l'application Flask après modification du .env")
    print("   2. Testez avec : python test_email_config.py")
    print("   3. Vérifiez les logs de l'application pour les erreurs détaillées")

print()
print("=" * 60)
