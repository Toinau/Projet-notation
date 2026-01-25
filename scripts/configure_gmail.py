#!/usr/bin/env python3
"""
Script pour configurer Gmail dans le fichier .env
Usage:
    python configure_gmail.py
    python configure_gmail.py email password
"""

import os
import sys

def configure_gmail(email=None, password=None):
    """Configure Gmail dans le fichier .env"""
    env_path = '.env'
    
    print("=== Configuration Gmail pour l'envoi d'emails ===\n")
    
    # Demander les informations si non fournies
    if not email:
        print("1. Adresse email Gmail:")
        email = input("   Email Gmail (ex: monemail@gmail.com): ").strip()
    
    if not email or '@' not in email:
        print("ERREUR: Adresse email invalide")
        return False
    
    if not password:
        print("\n2. Mot de passe d'application Gmail:")
        print("   IMPORTANT: Utilisez un mot de passe d'application, pas votre mot de passe Gmail normal!")
        print("   Pour créer un mot de passe d'application:")
        print("   - Allez sur https://myaccount.google.com/apppasswords")
        print("   - Ou: Google Account > Security > 2-Step Verification > App passwords")
        print("   - Créez un mot de passe pour 'Mail' et 'Other (Custom name)'")
        print("   - Copiez le mot de passe généré (16 caractères sans espaces)")
        password = input("   Mot de passe d'application: ").strip()
    
    if not password:
        print("ERREUR: Mot de passe requis")
        return False
    
    # Lire le fichier .env existant ou créer un nouveau
    lines = []
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    
    # Variables à mettre à jour/ajouter
    mail_vars = {
        'MAIL_SERVER': 'smtp.gmail.com',
        'MAIL_PORT': '587',
        'MAIL_USE_TLS': 'true',
        'MAIL_USERNAME': email,
        'MAIL_PASSWORD': password,
        'MAIL_DEFAULT_SENDER': email
    }
    
    # Mettre à jour ou ajouter les variables
    updated_lines = []
    mail_vars_found = {key: False for key in mail_vars.keys()}
    
    for line in lines:
        line_stripped = line.strip()
        updated = False
        
        for var_name, var_value in mail_vars.items():
            if line_stripped.startswith(f'{var_name}='):
                updated_lines.append(f'{var_name}={var_value}\n')
                mail_vars_found[var_name] = True
                updated = True
                break
        
        if not updated:
            updated_lines.append(line)
    
    # Ajouter les variables manquantes
    if not all(mail_vars_found.values()):
        # Chercher la section email ou ajouter après SECRET_KEY
        email_section_found = False
        for i, line in enumerate(updated_lines):
            if 'MAIL_' in line or '# Configuration email' in line:
                email_section_found = True
                # Insérer les variables manquantes après la dernière ligne MAIL_ ou après le commentaire
                insert_pos = i + 1
                for var_name, var_value in mail_vars.items():
                    if not mail_vars_found[var_name]:
                        updated_lines.insert(insert_pos, f'{var_name}={var_value}\n')
                        insert_pos += 1
                break
        
        if not email_section_found:
            # Chercher où insérer (après SECRET_KEY ou à la fin)
            insert_pos = len(updated_lines)
            for i, line in enumerate(updated_lines):
                if 'SECRET_KEY=' in line:
                    insert_pos = i + 1
                    break
            
            # Ajouter une nouvelle section email
            if insert_pos < len(updated_lines):
                updated_lines.insert(insert_pos, '\n# Configuration email (Gmail)\n')
                insert_pos += 1
            else:
                updated_lines.append('\n# Configuration email (Gmail)\n')
            
            for var_name, var_value in mail_vars.items():
                if not mail_vars_found[var_name]:
                    updated_lines.insert(insert_pos, f'{var_name}={var_value}\n')
                    insert_pos += 1
    
    # Écrire le fichier
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(updated_lines)
    
    print(f"\nOK Configuration Gmail sauvegardee dans {env_path}")
    print("\nVariables configurees:")
    print(f"  MAIL_SERVER=smtp.gmail.com")
    print(f"  MAIL_PORT=587")
    print(f"  MAIL_USE_TLS=true")
    print(f"  MAIL_USERNAME={email}")
    print(f"  MAIL_PASSWORD=*** (masque)")
    print(f"  MAIL_DEFAULT_SENDER={email}")
    
    print("\nProchaines etapes:")
    print("1. Redemarrez votre application Flask")
    print("2. Testez en creant un questionnaire")
    print("3. Verifiez que les emails sont bien envoyes")
    
    return True

if __name__ == '__main__':
    try:
        email = None
        password = None
        
        # Vérifier les arguments en ligne de commande
        if len(sys.argv) >= 3:
            email = sys.argv[1]
            password = sys.argv[2]
        elif len(sys.argv) == 2:
            print("Usage: python configure_gmail.py [email] [password]")
            print("Ou lancez sans arguments pour mode interactif")
            sys.exit(1)
        
        configure_gmail(email, password)
    except KeyboardInterrupt:
        print("\n\nConfiguration annulee")
        sys.exit(1)
    except Exception as e:
        print(f"\nERREUR: {e}")
        sys.exit(1)
