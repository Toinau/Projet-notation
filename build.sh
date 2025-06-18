set -o errexit  # Exit on error

pip install --upgrade pip
pip install -r requirements.txt

# Migrations de base de données
python -c "
import os
from app import app, db
with app.app_context():
    db.create_all()
    print('Base de données initialisée!')
"