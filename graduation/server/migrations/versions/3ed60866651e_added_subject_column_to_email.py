"""Added subject column to Email

Revision ID: 3ed60866651e
Revises: 9903210a33dc
Create Date: 2025-03-05 13:03:41.995893

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3ed60866651e'
down_revision = '9903210a33dc'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('email') as batch_op:
        batch_op.add_column(sa.Column('subject', sa.String(255), nullable=False, server_default="No Subject"))  # ✅ الحل هنا

def downgrade():
    with op.batch_alter_table('email') as batch_op:
        batch_op.drop_column('subject')
