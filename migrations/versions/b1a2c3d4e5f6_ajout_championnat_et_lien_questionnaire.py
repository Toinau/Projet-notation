"""ajout championnat et lien questionnaire

Revision ID: b1a2c3d4e5f6
Revises: 908208d1653e
Create Date: 2026-02-10

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b1a2c3d4e5f6'
down_revision = '908208d1653e'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('championship',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nom', sa.String(length=100), nullable=False),
        sa.Column('actif', sa.Boolean(), nullable=False, server_default='1'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nom')
    )
    with op.batch_alter_table('questionnaire', schema=None) as batch_op:
        batch_op.add_column(sa.Column('championship_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_questionnaire_championship', 'championship', ['championship_id'], ['id'])


def downgrade():
    with op.batch_alter_table('questionnaire', schema=None) as batch_op:
        batch_op.drop_constraint('fk_questionnaire_championship', type_='foreignkey')
        batch_op.drop_column('championship_id')
    op.drop_table('championship')
