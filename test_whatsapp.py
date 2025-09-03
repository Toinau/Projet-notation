#!/usr/bin/env python3
"""
Script de test pour l'envoi de messages WhatsApp
"""

from app import create_app, db
from app.models import User
from app.whatsapp_service import WhatsAppService

def test_whatsapp():
    app = create_app()
    
    with app.app_context():
        # Récupérer Antoine Piedagnel
        user = User.query.filter_by(prenom='Antoine', nom='Piedagnel').first()
        
        if not user:
            print("❌ Utilisateur Antoine Piedagnel non trouvé")
            return
        
        print(f"Utilisateur: {user.prenom} {user.nom}")
        print(f"Téléphone: {user.telephone}")
        print(f"Notifications SMS activées: {user.notifications_sms}")
        
        # Créer l'instance du service WhatsApp
        whatsapp_service = WhatsAppService()
        
        # Message de test
        message = """🧪 *Test WhatsApp*

Ceci est un message de test pour vérifier que les notifications WhatsApp fonctionnent correctement.

_Moyon Percy Vélo Club_"""
        
        print(f"\nEnvoi du message de test...")
        success, response = whatsapp_service.send_whatsapp_message(user.telephone, message)
        
        if success:
            print("✅ Message WhatsApp envoyé avec succès!")
            print(f"Réponse: {response}")
        else:
            print("❌ Erreur lors de l'envoi du message WhatsApp")
            print(f"Erreur: {response}")

if __name__ == "__main__":
    test_whatsapp() 