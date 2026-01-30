"""many_to_many_user_team

Revision ID: 908208d1653e
Revises: ee74da8f5f33
Create Date: 2026-01-30 11:58:08.146471

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '908208d1653e'
down_revision = 'ee74da8f5f33'
branch_labels = None
depends_on = None


def upgrade():
    # Créer la table de liaison user_team
    op.create_table('user_team',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['team.id'], ),
        sa.PrimaryKeyConstraint('user_id', 'team_id')
    )
    
    # Migrer les données existantes de team_id vers user_team
    connection = op.get_bind()
    connection.execute(sa.text("""
        INSERT INTO user_team (user_id, team_id)
        SELECT id, team_id
        FROM user
        WHERE team_id IS NOT NULL
    """))
    
    # Supprimer la colonne team_id et la foreign key
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_constraint('fk_user_team_id', type_='foreignkey')
        batch_op.drop_column('team_id')


def downgrade():
    # Recréer la colonne team_id
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('team_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_user_team_id', 'team', ['team_id'], ['id'])
    
    # Migrer les données de user_team vers team_id (prendre la première équipe si plusieurs)
    connection = op.get_bind()
    connection.execute(sa.text("""
        UPDATE user u
        SET team_id = (
            SELECT ut.team_id
            FROM user_team ut
            WHERE ut.user_id = u.id
            LIMIT 1
        )
    """))
    
    # Supprimer la table user_team
    op.drop_table('user_team')
