#!/usr/bin/env python3
"""
Script pour activer les notifications SMS pour Antoine Piedagnel
"""

from app import create_app, db
from app.models import User

def activate_notifications():
    app = create_app()
    
    with app.app_context():
        # Récupérer Antoine Piedagnel
        user = User.query.filter_by(prenom='Antoine', nom='Piedagnel').first()
        
        if not user:
            print("❌ Utilisateur Antoine Piedagnel non trouvé")
            return
        
        print(f"Utilisateur: {user.prenom} {user.nom}")
        print(f"Notifications SMS avant: {user.notifications_sms}")
        
        # Activer les notifications SMS
        user.notifications_sms = True
        db.session.add(user)
        db.session.commit()
        
        print(f"Notifications SMS après: {user.notifications_sms}")
        print("✅ Notifications SMS activées pour Antoine Piedagnel")

if __name__ == "__main__":
    activate_notifications() 