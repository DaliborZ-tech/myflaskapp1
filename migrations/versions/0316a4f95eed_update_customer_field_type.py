"""Update customer field type

Revision ID: 0316a4f95eed
Revises: 
Create Date: 2025-01-30 12:25:43.557777

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '0316a4f95eed'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('contacts', schema=None) as batch_op:
        batch_op.alter_column('customer', existing_type=sa.String(40),
                              type_=sa.Integer())

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('contacts', schema=None) as batch_op:
        batch_op.alter_column('customer',
               existing_type=sa.String(length=40),
               type_=mysql.INTEGER(),
               existing_nullable=True)

    # ### end Alembic commands ###
