from flask.cli import FlaskGroup
from app import create_app, db  # On importe la factory et l'instance db
from flask_migrate import Migrate

app = create_app()  # On utilise la factory
migrate = Migrate(app, db)
cli = FlaskGroup(app)

if __name__ == '__main__':
    cli()
