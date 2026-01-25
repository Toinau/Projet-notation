#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour aider à corriger le mot de passe d'application Gmail
"""

import os
import sys
import io
import re

# Forcer l'encodage UTF-8 pour Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def clean_app_password(password):
    """Nettoie le mot de passe d'application (supprime les espaces)"""
    if not password:
        return None
    # Supprimer tous les espaces
    cleaned = password.replace(' ', '').replace('\t', '').strip()
    return cleaned

def validate_app_password(password):
    """Valide le format d'un mot de passe d'application Gmail"""
    if not password:
        return False, "Le mot de passe est vide"
    
    # Un mot de passe d'application Gmail fait exactement 16 caractères
    if len(password) != 16:
        return False, f"Le mot de passe fait {len(password)} caractères (devrait être 16)"
    
    # Vérifier qu'il ne contient que des caractères alphanumériques
    if not re.match(r'^[a-zA-Z0-9]+$', password):
        return False, "Le mot de passe contient des caractères invalides (doit être alphanumérique)"
    
    return True, "Format valide"

def update_env_file(env_path, new_password):
    """Met à jour le mot de passe dans le fichier .env"""
    if not os.path.exists(env_path):
        print(f"❌ Fichier .env non trouvé : {env_path}")
        return False
    
    # Lire le fichier
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Mettre à jour la ligne MAIL_PASSWORD
    updated = False
    new_lines = []
    for line in lines:
        if line.strip().startswith('MAIL_PASSWORD=') or line.strip().startswith('mail_password='):
            # Extraire le nom de la variable (peut être en majuscules ou minuscules)
            var_name = 'MAIL_PASSWORD' if 'MAIL_PASSWORD' in line.upper() else 'MAIL_PASSWORD'
            new_lines.append(f"{var_name}={new_password}\n")
            updated = True
        else:
            new_lines.append(line)
    
    # Si la variable n'existe pas, l'ajouter
    if not updated:
        # Chercher où insérer (après MAIL_USERNAME ou à la fin de la section email)
        insert_pos = len(new_lines)
        for i, line in enumerate(new_lines):
            if 'MAIL_USERNAME=' in line.upper():
                insert_pos = i + 1
                break
        
        new_lines.insert(insert_pos, f"MAIL_PASSWORD={new_password}\n")
    
    # Écrire le fichier
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    return True

def main():
    print("=" * 70)
    print("CORRECTION DU MOT DE PASSE D'APPLICATION GMAIL")
    print("=" * 70)
    print()
    print("Ce script vous aide à configurer correctement votre mot de passe")
    print("d'application Gmail pour l'envoi d'emails.")
    print()
    print("=" * 70)
    print()
    
    # Vérifier si le fichier .env existe
    env_path = '.env'
    if not os.path.exists(env_path):
        print(f"❌ Fichier .env non trouvé : {os.path.abspath(env_path)}")
        print()
        print("💡 Créez d'abord un fichier .env avec :")
        print("   python configure_gmail.py")
        return 1
    
    print(f"✅ Fichier .env trouvé : {os.path.abspath(env_path)}")
    print()
    
    # Instructions
    print("📋 INSTRUCTIONS :")
    print("-" * 70)
    print("1. Allez sur : https://myaccount.google.com/apppasswords")
    print("2. Si vous n'avez pas activé l'authentification à deux facteurs,")
    print("   vous devrez d'abord l'activer :")
    print("   https://myaccount.google.com/security")
    print("3. Créez un nouveau mot de passe d'application :")
    print("   - Application : 'Mail'")
    print("   - Appareil : 'Autre (nom personnalisé)' → 'Flask App'")
    print("4. Copiez le mot de passe généré (16 caractères)")
    print()
    print("-" * 70)
    print()
    
    # Demander le nouveau mot de passe
    print("Entrez le nouveau mot de passe d'application Gmail :")
    print("(16 caractères, sans espaces - le script supprimera automatiquement les espaces)")
    password = input("> ").strip()
    
    if not password:
        print("❌ Aucun mot de passe fourni")
        return 1
    
    # Nettoyer le mot de passe
    cleaned_password = clean_app_password(password)
    
    # Valider le format
    is_valid, message = validate_app_password(cleaned_password)
    
    if not is_valid:
        print(f"❌ {message}")
        print()
        print("💡 Vérifiez que :")
        print("   - Le mot de passe fait exactement 16 caractères")
        print("   - Il ne contient que des lettres et chiffres (pas d'espaces)")
        print("   - Vous avez bien copié le mot de passe depuis Google")
        return 1
    
    print(f"✅ Format valide : {len(cleaned_password)} caractères")
    print()
    
    # Confirmer
    print(f"Le mot de passe sera mis à jour dans le fichier .env")
    confirm = input("Continuer ? (o/n) : ").strip().lower()
    
    if confirm not in ['o', 'oui', 'y', 'yes']:
        print("Annulé")
        return 0
    
    # Mettre à jour le fichier
    if update_env_file(env_path, cleaned_password):
        print()
        print("✅ Mot de passe mis à jour dans le fichier .env")
        print()
        print("⚠️  IMPORTANT : Redémarrez votre application Flask maintenant !")
        print()
        print("Pour tester la configuration :")
        print("  python test_email_config.py")
        return 0
    else:
        print("❌ Erreur lors de la mise à jour du fichier .env")
        return 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nAnnulé par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur : {e}")
        sys.exit(1)
