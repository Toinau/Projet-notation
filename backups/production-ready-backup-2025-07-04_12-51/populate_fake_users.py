# === Paramètres à personnaliser ===
NOMBRE_UTILISATEURS = 5  # Nombre d'utilisateurs à générer
ROLE = "coureur"           # Rôle : "coureur" ou "admin"
MOT_DE_PASSE = "test"    # Mot de passe pour tous

from app import db, create_app
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    ajoutés = 0
    for i in range(1, NOMBRE_UTILISATEURS + 1):
        prenom = f"Testeur{i}"
        nom = "Fictif"
        email = f"testeur{i}@test.com"
        if User.query.filter_by(email=email).first():
            print(f"Utilisateur avec l'email {email} existe déjà, on saute.")
            continue
        password = generate_password_hash(MOT_DE_PASSE)
        user = User(
            prenom=prenom,
            nom=nom,
            email=email,
            password=password,
            role=ROLE,
            is_active=True
        )
        db.session.add(user)
        ajoutés += 1
    db.session.commit()
    print(f"{ajoutés} nouveaux utilisateurs fictifs créés (les doublons ont été ignorés) avec le rôle '{ROLE}' et le mot de passe '{MOT_DE_PASSE}' !") 