from app import create_app, db
from app.models import Team

app = create_app()

with app.app_context():
    if not Team.query.filter_by(nom="Équipe A").first():
        team_a = Team(nom="Équipe A", description="Première équipe", couleur="#007bff", actif=True)
        db.session.add(team_a)
    if not Team.query.filter_by(nom="Équipe B").first():
        team_b = Team(nom="Équipe B", description="Deuxième équipe", couleur="#28a745", actif=True)
        db.session.add(team_b)
    db.session.commit()
    print("Équipes de base créées ou déjà existantes.") 