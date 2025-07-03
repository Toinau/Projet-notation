import click
from flask.cli import with_appcontext
from app.models import User
from app import db
from werkzeug.security import generate_password_hash

def register_cli(app):
    @app.cli.command('create-admin')
    @with_appcontext
    def create_admin():
        username = input("Nom d'utilisateur admin: ").strip()
        email = input("Email admin: ").strip().lower()
        password = input("Mot de passe admin: ")
        if not username or not email or not password:
            print("❌ Tous les champs sont requis")
            return
        if not User.validate_email(email):
            print("❌ Format d'email invalide")
            return
        is_valid_password, password_msg = User.validate_password(password)
        if not is_valid_password:
            print(f"❌ {password_msg}")
            return
        if User.query.filter_by(username=username).first():
            print("❌ Nom d'utilisateur déjà utilisé")
            return
        if User.query.filter_by(email=email).first():
            print("❌ Email déjà utilisé")
            return
        try:
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            admin_user = User(username=username, email=email, password=hashed_password, role='admin')
            db.session.add(admin_user)
            db.session.commit()
            print(f"✅ Administrateur {username} créé avec succès!")
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
                print(f"ID: {user.id} | Username: {user.username} | Email: {user.email} | Rôle: {user.role} | Statut: {status}")
            print(f"\nTotal: {len(users)} utilisateurs")
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des utilisateurs: {e}")

    @app.cli.command('check-user')
    @click.argument('username')
    @with_appcontext
    def check_user(username):
        try:
            user = User.query.filter_by(username=username).first()
            if user:
                print(f"\n=== Détails de l'utilisateur {username} ===")
                print(f"ID: {user.id}")
                print(f"Username: {user.username}")
                print(f"Email: {user.email}")
                print(f"Rôle: {user.role}")
                print(f"Actif: {user.is_active}")
                print(f"Créé le: {user.created_at}")
            else:
                print(f"❌ Utilisateur '{username}' non trouvé")
        except Exception as e:
            print(f"❌ Erreur lors de la vérification: {e}")

    @app.cli.command('fix-admin-role')
    @click.argument('username')
    @with_appcontext
    def fix_admin_role(username):
        try:
            user = User.query.filter_by(username=username).first()
            if user:
                user.role = 'admin'
                user.is_active = True
                db.session.commit()
                print(f"✅ Rôle admin forcé pour {username}")
                print(f"Nouveau rôle: {user.role}")
            else:
                print(f"❌ Utilisateur '{username}' non trouvé")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur lors de la modification: {e}")

    @app.cli.command('create-user')
    @click.option('--username', prompt='Nom d\'utilisateur')
    @click.option('--email', prompt='Email')
    @click.option('--password', prompt='Mot de passe', hide_input=True)
    @click.option('--role', default='coureur', type=click.Choice(['coureur', 'admin']))
    @with_appcontext
    def create_user(username, email, password, role):
        if not User.validate_email(email):
            print("❌ Format d'email invalide")
            return
        is_valid_password, password_msg = User.validate_password(password)
        if not is_valid_password:
            print(f"❌ {password_msg}")
            return
        if User.query.filter_by(username=username).first():
            print("❌ Nom d'utilisateur déjà utilisé")
            return
        if User.query.filter_by(email=email).first():
            print("❌ Email déjà utilisé")
            return
        try:
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(username=username, email=email, password=hashed_password, role=role)
            db.session.add(new_user)
            db.session.commit()
            print(f"✅ Utilisateur {username} ({role}) créé avec succès!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur lors de la création: {e}")

    @app.cli.command('delete-user')
    @click.argument('username')
    @click.option('--force', is_flag=True, help='Supprimer sans confirmation')
    @with_appcontext
    def delete_user_cli(username, force):
        try:
            user = User.query.filter_by(username=username).first()
            if not user:
                print(f"❌ Utilisateur '{username}' non trouvé")
                return
            if not force:
                confirm = input(f"Êtes-vous sûr de vouloir supprimer l'utilisateur '{username}' ? (y/N): ")
                if confirm.lower() != 'y':
                    print("❌ Suppression annulée")
                    return
            db.session.delete(user)
            db.session.commit()
            print(f"✅ Utilisateur '{username}' supprimé avec succès")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur lors de la suppression: {e}")

    @app.cli.command('toggle-user-status')
    @click.argument('username')
    @with_appcontext
    def toggle_user_status_cli(username):
        try:
            user = User.query.filter_by(username=username).first()
            if not user:
                print(f"❌ Utilisateur '{username}' non trouvé")
                return
            user.is_active = not user.is_active
            status = "activé" if user.is_active else "désactivé"
            db.session.commit()
            print(f"✅ Utilisateur '{username}' {status}")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur lors de la modification: {e}")

    @app.cli.command('change-user-role')
    @click.argument('username')
    @click.option('--role', type=click.Choice(['coureur', 'admin']), required=True)
    @with_appcontext
    def change_user_role(username, role):
        try:
            user = User.query.filter_by(username=username).first()
            if not user:
                print(f"❌ Utilisateur '{username}' non trouvé")
                return
            old_role = user.role
            user.role = role
            db.session.commit()
            print(f"✅ Rôle de '{username}' changé de '{old_role}' vers '{role}'")
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