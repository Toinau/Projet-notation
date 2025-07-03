#!/usr/bin/env python3
"""
Script pour tester rapidement l'application avec différents comptes
Génère des liens de connexion directe pour faciliter les tests
"""

from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()

def create_test_accounts():
    """Crée des comptes de test si ils n'existent pas"""
    with app.app_context():
        # Compte admin de test
        admin_email = "admin@test.com"
        if not User.query.filter_by(email=admin_email).first():
            admin = User(
                prenom="Admin",
                nom="Test",
                email=admin_email,
                password=generate_password_hash("test"),
                role="admin",
                is_active=True
            )
            db.session.add(admin)
            print("✅ Compte admin créé: admin@test.com / test")
        
        # Compte coureur de test
        coureur_email = "coureur@test.com"
        if not User.query.filter_by(email=coureur_email).first():
            coureur = User(
                prenom="Coureur",
                nom="Test",
                email=coureur_email,
                password=generate_password_hash("test"),
                role="coureur",
                is_active=True
            )
            db.session.add(coureur)
            print("✅ Compte coureur créé: coureur@test.com / test")
        
        db.session.commit()

def show_test_instructions():
    """Affiche les instructions pour tester avec plusieurs comptes"""
    print("\n" + "="*60)
    print("🎯 INSTRUCTIONS POUR TESTER AVEC PLUSIEURS COMPTES")
    print("="*60)
    print()
    print("📋 MÉTHODE 1 - Onglets privés (RECOMMANDÉE):")
    print("   1. Ouvre un onglet normal → Connecte-toi en admin")
    print("   2. Ouvre un onglet privé → Connecte-toi en coureur")
    print("   3. Chaque onglet aura sa propre session !")
    print()
    print("📋 MÉTHODE 2 - Navigateurs différents:")
    print("   - Chrome pour l'admin")
    print("   - Firefox/Edge pour le coureur")
    print()
    print("📋 MÉTHODE 3 - Profils de navigateur:")
    print("   - Profil 1 pour l'admin")
    print("   - Profil 2 pour le coureur")
    print()
    print("🔑 COMPTES DE TEST DISPONIBLES:")
    print("   👑 Admin:    admin@test.com / test")
    print("   🏃 Coureur:  coureur@test.com / test")
    print()
    print("💡 ASTUCE: Tu peux aussi utiliser les comptes générés par populate_fake_users.py")
    print("   Ex: testeur1@test.com / test, testeur2@test.com / test, etc.")
    print()
    print("🌐 URL de l'application: http://localhost:5000")
    print("="*60)

if __name__ == "__main__":
    create_test_accounts()
    show_test_instructions() 