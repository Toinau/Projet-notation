#!/usr/bin/env python3
"""
Script pour mettre à jour le Phone Number ID WhatsApp dans .env
"""

import sys
import os

def update_env_phone_id(phone_id, env_path='.env'):
    """Met à jour le Phone Number ID dans le fichier .env"""
    lines = []
    found = False
    
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('WHATSAPP_PHONE_NUMBER_ID='):
                    lines.append(f'WHATSAPP_PHONE_NUMBER_ID={phone_id}\n')
                    found = True
                else:
                    lines.append(line)
    
    if not found:
        lines.append(f'WHATSAPP_PHONE_NUMBER_ID={phone_id}\n')
    
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"OK Phone Number ID mis a jour dans {env_path}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python update_whatsapp_phone_id.py <PHONE_NUMBER_ID>")
        print("\nOu entrez le Phone Number ID maintenant:")
        phone_id = input("Phone Number ID: ").strip()
    else:
        phone_id = sys.argv[1]
    
    if phone_id:
        update_env_phone_id(phone_id)
    else:
        print("ERREUR: Phone Number ID vide")

