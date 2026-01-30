#!/usr/bin/env python3
"""
Script pour vérifier et corriger les numéros de téléphone dans la base de données
"""

import os
import sys
from app import create_app, db
from app.models import User
import re

def clean_phone_number(phone_number):
    """Nettoie et formate le numéro de téléphone (SMS / international)"""
    if not phone_number:
        return None
    
    # Supprimer les espaces, tirets, points et parenthèses
    cleaned = re.sub(r'[\s\-\.\(\)]', '', phone_number)
    
    # Supprimer tous les caractères non numériques sauf le +
    cleaned = re.sub(r'[^\d\+]', '', cleaned)
    
    # Gestion des formats français
    if cleaned.startswith('0'):
        # Format 06 12 34 56 78 -> +33612345678
        cleaned = '+33' + cleaned[1:]
    elif cleaned.startswith('33') and not cleaned.startswith('+33'):
        # Format 33 6 12 34 56 78 -> +33612345678
        cleaned = '+' + cleaned
    elif not cleaned.startswith('+33'):
        # Si pas d'indicatif, ajouter +33
        cleaned = '+33' + cleaned
    
    # Vérifier que le numéro fait 12 caractères (+33 + 9 chiffres)
    if len(cleaned) != 12 or not cleaned.startswith('+33'):
        return None
        
    return cleaned

def main():
    app = create_app()
    
    with app.app_context():
        # Récupérer tous les utilisateurs avec un numéro de téléphone
        users = User.query.filter(User.telephone.isnot(None)).all()
        
        print(f"Vérification de {len(users)} utilisateurs avec numéro de téléphone:")
        print("-" * 60)
        
        for user in users:
            original = user.telephone
            cleaned = clean_phone_number(original)
            
            print(f"Utilisateur: {user.prenom} {user.nom}")
            print(f"  Numéro original: {original}")
            print(f"  Numéro formaté: {cleaned}")
            
            if cleaned and cleaned != original:
                print(f"  ✅ Correction nécessaire")
                user.telephone = cleaned
                db.session.add(user)
            elif cleaned:
                print(f"  ✅ Format correct")
            else:
                print(f"  ❌ Format invalide")
            
            print()
        
        # Sauvegarder les modifications
        try:
            db.session.commit()
            print("✅ Modifications sauvegardées dans la base de données")
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")
            db.session.rollback()

if __name__ == "__main__":
    main() 