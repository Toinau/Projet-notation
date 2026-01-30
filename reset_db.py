#!/usr/bin/env python3
"""
Remet la base de données à zéro : supprime tous les utilisateurs, équipes et évènements (questionnaires).
À utiliser pour préparer une mise en production avec une base vide.

Usage : python reset_db.py
        python reset_db.py --force   (sans demande de confirmation)
"""
import sys

def reset_database(force=False):
    from app import create_app, db
    from app.models import (
        QuestionnaireResponse,
        QuestionnaireParticipant,
        Questionnaire,
        User,
        Team,
        user_team,
    )

    if not force:
        rep = input("Supprimer TOUTES les données (utilisateurs, équipes, évènements) ? Tapez 'oui' pour confirmer : ").strip().lower()
        if rep != "oui":
            print("Annulé.")
            return 0

    app = create_app()
    with app.app_context():
        try:
            # Ordre de suppression pour respecter les clés étrangères
            nb_responses = db.session.query(QuestionnaireResponse).delete()
            nb_participants = db.session.query(QuestionnaireParticipant).delete()
            nb_questionnaires = db.session.query(Questionnaire).delete()
            nb_user_team = db.session.execute(user_team.delete()).rowcount
            nb_users = db.session.query(User).delete()
            nb_teams = db.session.query(Team).delete()

            db.session.commit()

            print("Base de données réinitialisée avec succès.")
            print(f"  - Réponses aux questionnaires : {nb_responses}")
            print(f"  - Participations : {nb_participants}")
            print(f"  - Questionnaires / évènements : {nb_questionnaires}")
            print(f"  - Liaisons utilisateur-équipe : {nb_user_team}")
            print(f"  - Utilisateurs : {nb_users}")
            print(f"  - Équipes : {nb_teams}")
            print("\nLa base est vide. Créez un compte admin avec : flask create-admin")
            return 0
        except Exception as e:
            db.session.rollback()
            print(f"Erreur lors de la réinitialisation : {e}", file=sys.stderr)
            return 1


if __name__ == "__main__":
    force = "--force" in sys.argv or "-f" in sys.argv
    sys.exit(reset_database(force=force))
