#!/usr/bin/env python3
"""
Script de test pour l'envoi du template WhatsApp hello_world
"""

from app import create_app, db
from app.models import User
from app.whatsapp_service import WhatsAppService

def test_hello_world_template():
    app = create_app()
    
    with app.app_context():
        # Récupérer Antoine Piedagnel
        user = User.query.filter_by(prenom='Antoine', nom='Piedagnel').first()
        
        if not user:
            print("❌ Utilisateur Antoine Piedagnel non trouvé")
            return
        
        whatsapp_service = WhatsAppService()
        clean_number = whatsapp_service._clean_phone_number(user.telephone)
        
        print(f"Envoi du template hello_world à {clean_number}...")
        success, response = whatsapp_service.send_hello_world_template(clean_number)
        if success:
            print("✅ Template hello_world envoyé avec succès!")
            print(f"Réponse: {response}")
        else:
            print("❌ Erreur lors de l'envoi du template hello_world")
            print(f"Erreur: {response}")

if __name__ == "__main__":
    test_hello_world_template() 