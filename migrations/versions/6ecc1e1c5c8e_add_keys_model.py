"""Add keys model

Revision ID: 6ecc1e1c5c8e
Revises: 8b9e574126ce
Create Date: 2023-04-03 20:52:55.201137

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6ecc1e1c5c8e'
down_revision = '8b9e574126ce'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('activation_keys',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('key', sa.String(length=70), nullable=False),
    sa.Column('name', sa.String(length=70), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('activation_keys')
    # ### end Alembic commands ###
