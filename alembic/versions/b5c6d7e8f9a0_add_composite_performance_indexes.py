"""add composite performance indexes

Revision ID: b5c6d7e8f9a0
Revises: a2b4c6d8e0f1
Create Date: 2026-08-10 23:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b5c6d7e8f9a0'
down_revision: Union[str, Sequence[str], None] = 'a2b4c6d8e0f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add composite index for filtering transactions by user and date
    op.create_index(
        'ix_transactions_user_id_date',
        'transactions',
        ['user_id', 'date'],
        unique=False
    )
    # Add composite index for fetching chat history by user and conversation
    op.create_index(
        'ix_chat_messages_user_id_conversation_id',
        'chat_messages',
        ['user_id', 'conversation_id'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index('ix_chat_messages_user_id_conversation_id', table_name='chat_messages')
    op.drop_index('ix_transactions_user_id_date', table_name='transactions')
