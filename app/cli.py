import click
from flask.cli import with_appcontext
from app.models import User
from app import db
from werkzeug.security import generate_password_hash

def register_cli(app):
    @app.cli.command('create-admin')
    @click.option('--prenom', '-p', default=None, help='Prénom de l\'administrateur')
    @click.option('--nom', '-n', default=None, help='Nom de l\'administrateur')
    @click.option('--email', '-e', default=None, help='Email de l\'administrateur')
    @click.option('--password', '-w', default=None, help='Mot de passe (8+ car., 1 maj., 1 min., 1 chiffre)')
    @with_appcontext
    def create_admin(prenom, nom, email, password):
        if prenom is None:
            prenom = input("Prénom admin: ").strip()
        if nom is None:
            nom = input("Nom admin: ").strip()
        if email is None:
            email = input("Email admin: ").strip().lower()
        else:
            email = email.strip().lower()
        if password is None:
            password = input("Mot de passe admin: ")
        if not prenom or not nom or not email or not password:
            print("❌ Tous les champs sont requis")
            return
        if not User.validate_email(email):
            print("❌ Format d'email invalide")
            return
        is_valid_password, password_msg = User.validate_password(password)
        if not is_valid_password:
            print(f"❌ {password_msg}")
            return
        if User.query.filter_by(prenom=prenom, nom=nom).first():
            print("❌ Nom d'utilisateur déjà utilisé")
            return
        if User.query.filter_by(email=email).first():
            print("❌ Email déjà utilisé")
            return
        try:
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            admin_user = User(prenom=prenom, nom=nom, email=email, password=hashed_password, role='admin')
            db.session.add(admin_user)
            db.session.commit()
            print(f"✅ Administrateur {prenom} {nom} créé avec succès!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur lors de la création: {e}")

    @app.cli.command('list-users')
    @with_appcontext
    def list_users():
        try:
            users = User.query.all()
            print("\n=== Liste des utilisateurs ===")
            for user in users:
                status = "Actif" if user.is_active else "Inactif"
                print(f"ID: {user.id} | Prénom: {user.prenom} | Nom: {user.nom} | Email: {user.email} | Rôle: {user.role} | Statut: {status}")
            print(f"\nTotal: {len(users)} utilisateurs")
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des utilisateurs: {e}")

    @app.cli.command('check-user')
    @click.argument('prenom')
    @click.argument('nom')
    @with_appcontext
    def check_user(prenom, nom):
        try:
            user = User.query.filter_by(prenom=prenom, nom=nom).first()
            if user:
                print(f"\n=== Détails de l'utilisateur {prenom} {nom} ===")
                print(f"ID: {user.id}")
                print(f"Prénom: {user.prenom}")
                print(f"Nom: {user.nom}")
                print(f"Email: {user.email}")
                print(f"Rôle: {user.role}")
                print(f"Actif: {user.is_active}")
                print(f"Créé le: {user.created_at}")
            else:
                print(f"❌ Utilisateur '{prenom} {nom}' non trouvé")
        except Exception as e:
            print(f"❌ Erreur lors de la vérification: {e}")

    @app.cli.command('fix-admin-role')
    @click.argument('prenom')
    @click.argument('nom')
    @with_appcontext
    def fix_admin_role(prenom, nom):
        try:
            user = User.query.filter_by(prenom=prenom, nom=nom).first()
            if user:
                user.role = 'admin'
                user.is_active = True
                db.session.commit()
                print(f"✅ Rôle admin forcé pour {prenom} {nom}")
                print(f"Nouveau rôle: {user.role}")
            else:
                print(f"❌ Utilisateur '{prenom} {nom}' non trouvé")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur lors de la modification: {e}")

    @app.cli.command('create-user')
    @click.option('--prenom', prompt='Prénom')
    @click.option('--nom', prompt='Nom')
    @click.option('--email', prompt='Email')
    @click.option('--password', prompt='Mot de passe', hide_input=True)
    @click.option('--role', default='coureur', type=click.Choice(['coureur', 'admin']))
    @with_appcontext
    def create_user(prenom, nom, email, password, role):
        if not User.validate_email(email):
            print("❌ Format d'email invalide")
            return
        is_valid_password, password_msg = User.validate_password(password)
        if not is_valid_password:
            print(f"❌ {password_msg}")
            return
        if User.query.filter_by(prenom=prenom, nom=nom).first():
            print("❌ Nom d'utilisateur déjà utilisé")
            return
        if User.query.filter_by(email=email).first():
            print("❌ Email déjà utilisé")
            return
        try:
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(prenom=prenom, nom=nom, email=email, password=hashed_password, role=role)
            db.session.add(new_user)
            db.session.commit()
            print(f"✅ Utilisateur {prenom} {nom} ({role}) créé avec succès!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur lors de la création: {e}")

    @app.cli.command('delete-user')
    @click.argument('prenom')
    @click.argument('nom')
    @click.option('--force', is_flag=True, help='Supprimer sans confirmation')
    @with_appcontext
    def delete_user_cli(prenom, nom, force):
        try:
            user = User.query.filter_by(prenom=prenom, nom=nom).first()
            if not user:
                print(f"❌ Utilisateur '{prenom} {nom}' non trouvé")
                return
            if not force:
                confirm = input(f"Êtes-vous sûr de vouloir supprimer l'utilisateur '{prenom} {nom}' ? (y/N): ")
                if confirm.lower() != 'y':
                    print("❌ Suppression annulée")
                    return
            db.session.delete(user)
            db.session.commit()
            print(f"✅ Utilisateur '{prenom} {nom}' supprimé avec succès")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur lors de la suppression: {e}")

    @app.cli.command('toggle-user-status')
    @click.argument('prenom')
    @click.argument('nom')
    @with_appcontext
    def toggle_user_status_cli(prenom, nom):
        try:
            user = User.query.filter_by(prenom=prenom, nom=nom).first()
            if not user:
                print(f"❌ Utilisateur '{prenom} {nom}' non trouvé")
                return
            user.is_active = not user.is_active
            status = "activé" if user.is_active else "désactivé"
            db.session.commit()
            print(f"✅ Utilisateur '{prenom} {nom}' {status}")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur lors de la modification: {e}")

    @app.cli.command('change-user-role')
    @click.argument('prenom')
    @click.argument('nom')
    @click.option('--role', type=click.Choice(['coureur', 'admin']), required=True)
    @with_appcontext
    def change_user_role(prenom, nom, role):
        try:
            user = User.query.filter_by(prenom=prenom, nom=nom).first()
            if not user:
                print(f"❌ Utilisateur '{prenom} {nom}' non trouvé")
                return
            old_role = user.role
            user.role = role
            db.session.commit()
            print(f"✅ Rôle de '{prenom} {nom}' changé de '{old_role}' vers '{role}'")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur lors du changement de rôle: {e}")

    @app.cli.command('init-db')
    @with_appcontext
    def init_db_command():
        try:
            db.create_all()
            print('✅ Base de données initialisée.')
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation: {e}")

    @app.cli.command('reset-db')
    @click.option('--force', is_flag=True, help='Réinitialiser sans confirmation')
    @with_appcontext
    def reset_db_command(force):
        if not force:
            confirm = input("⚠️  ATTENTION: Cela supprimera toutes les données. Continuer ? (y/N): ")
            if confirm.lower() != 'y':
                print("❌ Réinitialisation annulée")
                return
        try:
            db.drop_all()
            db.create_all()
            print('✅ Base de données réinitialisée.')
        except Exception as e:
            print(f"❌ Erreur lors de la réinitialisation: {e}")

    @app.cli.command('db-stats')
    @with_appcontext
    def db_stats():
        try:
            total_users = User.query.count()
            total_coureurs = User.query.filter_by(role='coureur').count()
            total_admins = User.query.filter_by(role='admin').count()
            active_users = User.query.filter_by(is_active=True).count()
            inactive_users = User.query.filter_by(is_active=False).count()
            print("\n=== Statistiques de la base de données ===")
            print(f"Total utilisateurs: {total_users}")
            print(f"Coureurs: {total_coureurs}")
            print(f"Administrateurs: {total_admins}")
            print(f"Utilisateurs actifs: {active_users}")
            print(f"Utilisateurs inactifs: {inactive_users}")
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des statistiques: {e}") 