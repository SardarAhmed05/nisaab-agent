"""make username nullable

Revision ID: 8a4d1072ce76
Revises: 83ccf89062d9
Create Date: 2026-07-22 11:47:45.325976

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8a4d1072ce76'
down_revision: Union[str, Sequence[str], None] = '83ccf89062d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('username',
                   existing_type=sa.VARCHAR(length=25),
                   nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('username',
                   existing_type=sa.VARCHAR(length=25),
                   nullable=False)
