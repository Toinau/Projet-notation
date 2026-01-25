#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de diagnostic pour tester la configuration email Gmail
"""

import os
import sys
import io

# Forcer l'encodage UTF-8 pour Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from dotenv import load_dotenv
from flask_mail import Mail, Message
from flask import Flask

# Charger le fichier .env
load_dotenv()

print("=" * 60)
print("DIAGNOSTIC DE CONFIGURATION EMAIL GMAIL")
print("=" * 60)
print()

# Vérifier si le fichier .env existe
env_path = '.env'
if os.path.exists(env_path):
    print(f"✅ Fichier .env trouvé : {os.path.abspath(env_path)}")
else:
    print(f"❌ Fichier .env NON TROUVÉ à : {os.path.abspath(env_path)}")
    print("   Créez un fichier .env à la racine du projet")
    sys.exit(1)

print()

# Vérifier les variables d'environnement
print("📋 Vérification des variables d'environnement :")
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
for var_name, var_value in mail_vars.items():
    if var_value:
        if var_name == 'MAIL_PASSWORD':
            # Masquer le mot de passe mais afficher sa longueur
            masked = '*' * min(len(var_value), 20)
            if len(var_value) > 20:
                masked += f" ({len(var_value)} caractères)"
            else:
                masked += f" ({len(var_value)} caractères)"
            print(f"  ✅ {var_name}: {masked}")
            
            # Vérifier s'il y a des espaces
            if ' ' in var_value:
                print(f"     ⚠️  ATTENTION : Le mot de passe contient des espaces !")
                print(f"     Supprimez les espaces du mot de passe d'application")
                all_ok = False
            
            # Vérifier la longueur (un mot de passe d'application Gmail fait 16 caractères)
            if len(var_value) != 16:
                print(f"     ⚠️  ATTENTION : Un mot de passe d'application Gmail fait 16 caractères")
                print(f"     Longueur actuelle : {len(var_value)} caractères")
        else:
            print(f"  ✅ {var_name}: {var_value}")
    else:
        print(f"  ❌ {var_name}: NON DÉFINI")
        all_ok = False

print()

if not all_ok:
    print("❌ Certaines variables sont manquantes ou incorrectes")
    print()
    print("💡 Solution :")
    print("   1. Vérifiez que toutes les variables sont définies dans le fichier .env")
    print("   2. Utilisez un mot de passe d'application Gmail (16 caractères, sans espaces)")
    print("   3. Exécutez : python configure_gmail.py")
    sys.exit(1)

print("✅ Toutes les variables sont définies")
print()

# Créer une application Flask minimale pour tester
print("🔧 Configuration de Flask-Mail :")
print("-" * 60)

app = Flask(__name__)
app.config['MAIL_SERVER'] = mail_vars['MAIL_SERVER'] or 'smtp.gmail.com'
app.config['MAIL_PORT'] = int(mail_vars['MAIL_PORT'] or 587)
app.config['MAIL_USE_TLS'] = mail_vars['MAIL_USE_TLS'] and mail_vars['MAIL_USE_TLS'].lower() in ['true', 'on', '1']
app.config['MAIL_USERNAME'] = mail_vars['MAIL_USERNAME']
app.config['MAIL_PASSWORD'] = mail_vars['MAIL_PASSWORD']
app.config['MAIL_DEFAULT_SENDER'] = mail_vars['MAIL_DEFAULT_SENDER'] or mail_vars['MAIL_USERNAME']

print(f"  Serveur SMTP : {app.config['MAIL_SERVER']}")
print(f"  Port : {app.config['MAIL_PORT']}")
print(f"  TLS : {app.config['MAIL_USE_TLS']}")
print(f"  Utilisateur : {app.config['MAIL_USERNAME']}")
print(f"  Expéditeur : {app.config['MAIL_DEFAULT_SENDER']}")

mail = Mail(app)
mail.init_app(app)

print()
print("📧 Test d'envoi d'email :")
print("-" * 60)

# Demander l'adresse email de test
test_email = input("Entrez votre adresse email pour recevoir un email de test (ou appuyez sur Entrée pour annuler) : ").strip()

if not test_email:
    print("Test annulé")
    sys.exit(0)

if '@' not in test_email:
    print("❌ Adresse email invalide")
    sys.exit(1)

try:
    with app.app_context():
        msg = Message(
            subject='Test de configuration email',
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=[test_email]
        )
        msg.body = """
Ceci est un email de test pour vérifier la configuration Gmail.

Si vous recevez cet email, la configuration est correcte !
        """
        
        print(f"  Envoi de l'email à {test_email}...")
        mail.send(msg)
        print("  ✅ Email envoyé avec succès !")
        print()
        print("  Vérifiez votre boîte de réception (et les spams)")
        
except Exception as e:
    error_msg = str(e)
    print(f"  ❌ Erreur lors de l'envoi : {error_msg}")
    print()
    
    if '535' in error_msg or 'BadCredentials' in error_msg or 'Username and Password not accepted' in error_msg:
        print("  🔍 DIAGNOSTIC : Erreur d'authentification Gmail")
        print()
        print("  💡 Solutions possibles :")
        print("     1. Vérifiez que vous utilisez un MOT DE PASSE D'APPLICATION (16 caractères)")
        print("        et non votre mot de passe Gmail normal")
        print("     2. Vérifiez qu'il n'y a pas d'espaces dans le mot de passe")
        print("     3. Vérifiez que l'authentification à deux facteurs est activée")
        print("     4. Créez un nouveau mot de passe d'application :")
        print("        https://myaccount.google.com/apppasswords")
        print("     5. Redémarrez votre application Flask après modification du .env")
    elif 'Connection' in error_msg or 'timeout' in error_msg.lower():
        print("  🔍 DIAGNOSTIC : Problème de connexion réseau")
        print("     Vérifiez votre connexion internet")
    else:
        print("  🔍 DIAGNOSTIC : Erreur inconnue")
        print(f"     Détails : {error_msg}")
    
    sys.exit(1)

print()
print("=" * 60)
print("✅ Test terminé avec succès !")
print("=" * 60)
