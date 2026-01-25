#!/usr/bin/env python3
"""
Script pour récupérer le Phone Number ID WhatsApp depuis l'API Graph
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

def get_phone_number_id():
    """Récupère le Phone Number ID depuis l'API Graph"""
    access_token = os.environ.get('WHATSAPP_ACCESS_TOKEN')
    
    if not access_token:
        print("ERREUR: WHATSAPP_ACCESS_TOKEN non trouve dans .env")
        return None
    
    # Récupérer les numéros de téléphone associés au compte
    url = "https://graph.facebook.com/v18.0/me/phone_numbers"
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and len(data['data']) > 0:
                phone_number_id = data['data'][0].get('id')
                phone_number = data['data'][0].get('verified_name') or data['data'][0].get('display_phone_number')
                print(f"Phone Number ID trouve: {phone_number_id}")
                print(f"Numero associe: {phone_number}")
                return phone_number_id
            else:
                print("Aucun numero de telephone trouve")
                return None
        else:
            print(f"ERREUR API: {response.status_code}")
            print(f"Reponse: {response.text}")
            
            # Essayer une autre méthode : récupérer depuis l'app WhatsApp
            if response.status_code == 400:
                print("\nTentative alternative: recuperation depuis l'application WhatsApp...")
                # Cette méthode nécessite l'ID de l'application
                # On va essayer de récupérer depuis les numéros WhatsApp Business
                url_alt = "https://graph.facebook.com/v18.0/me/whatsapp_business_accounts"
                response_alt = requests.get(url_alt, headers=headers)
                
                if response_alt.status_code == 200:
                    data_alt = response_alt.json()
                    if 'data' in data_alt and len(data_alt['data']) > 0:
                        waba_id = data_alt['data'][0].get('id')
                        print(f"WABA ID trouve: {waba_id}")
                        
                        # Récupérer les numéros de ce compte
                        url_phones = f"https://graph.facebook.com/v18.0/{waba_id}/phone_numbers"
                        response_phones = requests.get(url_phones, headers=headers)
                        
                        if response_phones.status_code == 200:
                            data_phones = response_phones.json()
                            if 'data' in data_phones and len(data_phones['data']) > 0:
                                phone_number_id = data_phones['data'][0].get('id')
                                print(f"Phone Number ID trouve: {phone_number_id}")
                                return phone_number_id
            
            return None
            
    except Exception as e:
        print(f"ERREUR: {e}")
        return None

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
    
    print(f"Phone Number ID mis a jour dans {env_path}")

if __name__ == '__main__':
    print("Recuperation du Phone Number ID WhatsApp...")
    phone_id = get_phone_number_id()
    
    if phone_id:
        print(f"\nPhone Number ID: {phone_id}")
        update = input("\nMettre a jour le fichier .env avec ce Phone Number ID ? (o/n): ")
        if update.lower() in ['o', 'oui', 'y', 'yes']:
            update_env_phone_id(phone_id)
            print("OK Configuration mise a jour!")
        else:
            print("Phone Number ID non mis a jour. Vous pouvez le mettre manuellement dans .env:")
            print(f"WHATSAPP_PHONE_NUMBER_ID={phone_id}")
    else:
        print("\nERREUR: Impossible de recuperer le Phone Number ID")
        print("\nAlternative: Recuperez-le manuellement depuis Meta:")
        print("1. Allez sur https://developers.facebook.com")
        print("2. Selectionnez votre application")
        print("3. WhatsApp > Configuration")
        print("4. Dans 'Numero de telephone', copiez l'ID (un nombre long)")

