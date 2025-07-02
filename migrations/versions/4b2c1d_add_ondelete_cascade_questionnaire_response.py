"""
Ajout de ON DELETE CASCADE sur questionnaire_response.questionnaire_id (compatible SQLite)
"""
from alembic import op
import sqlalchemy as sa

# révision et dépendance
revision = 'xxxx_add_ondelete_cascade_questionnaire_response'
down_revision = '3ca45965f90e'
branch_labels = None
depends_on = None

def upgrade():
    # 1. Créer la nouvelle table avec la bonne contrainte
    op.create_table(
        'questionnaire_response_tmp',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('questionnaire_id', sa.Integer, sa.ForeignKey('questionnaire.id', ondelete='CASCADE'), nullable=False),
        sa.Column('evaluator_id', sa.Integer, sa.ForeignKey('user.id'), nullable=False),
        sa.Column('evaluated_id', sa.Integer, sa.ForeignKey('user.id'), nullable=False),
        sa.Column('rating', sa.Integer, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=True)
    )
    # 2. Copier les données
    op.execute('''
        INSERT INTO questionnaire_response_tmp (id, questionnaire_id, evaluator_id, evaluated_id, rating, created_at)
        SELECT id, questionnaire_id, evaluator_id, evaluated_id, rating, created_at FROM questionnaire_response
    ''')
    # 3. Supprimer l'ancienne table
    op.drop_table('questionnaire_response')
    # 4. Renommer la nouvelle
    op.rename_table('questionnaire_response_tmp', 'questionnaire_response')

def downgrade():
    # 1. Recréer l'ancienne table sans ON DELETE CASCADE
    op.create_table(
        'questionnaire_response_old',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('questionnaire_id', sa.Integer, sa.ForeignKey('questionnaire.id'), nullable=False),
        sa.Column('evaluator_id', sa.Integer, sa.ForeignKey('user.id'), nullable=False),
        sa.Column('evaluated_id', sa.Integer, sa.ForeignKey('user.id'), nullable=False),
        sa.Column('rating', sa.Integer, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=True)
    )
    # 2. Copier les données
    op.execute('''
        INSERT INTO questionnaire_response_old (id, questionnaire_id, evaluator_id, evaluated_id, rating, created_at)
        SELECT id, questionnaire_id, evaluator_id, evaluated_id, rating, created_at FROM questionnaire_response
    ''')
    # 3. Supprimer la table modifiée
    op.drop_table('questionnaire_response')
    # 4. Renommer l'ancienne
    op.rename_table('questionnaire_response_old', 'questionnaire_response') 