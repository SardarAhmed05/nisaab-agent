"""add chat conversations

Revision ID: a2b4c6d8e0f1
Revises: f1a3c6d8e9b0
Create Date: 2026-08-10 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a2b4c6d8e0f1"
down_revision: Union[str, Sequence[str], None] = "f1a3c6d8e9b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "chat_conversations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_chat_conversations_user_id"), "chat_conversations", ["user_id"], unique=False)
    op.add_column("chat_messages", sa.Column("conversation_id", sa.Integer(), nullable=True))

    op.execute("""
        INSERT INTO chat_conversations (user_id, title, created_at, updated_at)
        SELECT user_id, 'Previous chat', MIN(created_at), MAX(created_at)
        FROM chat_messages
        GROUP BY user_id
    """)
    op.execute("""
        UPDATE chat_messages AS message
        SET conversation_id = conversation.id
        FROM chat_conversations AS conversation
        WHERE conversation.user_id = message.user_id
          AND conversation.title = 'Previous chat'
          AND message.conversation_id IS NULL
    """)

    op.alter_column("chat_messages", "conversation_id", nullable=False)
    op.create_foreign_key(
        "fk_chat_messages_conversation_id",
        "chat_messages",
        "chat_conversations",
        ["conversation_id"],
        ["id"],
    )
    op.create_index(op.f("ix_chat_messages_conversation_id"), "chat_messages", ["conversation_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_chat_messages_conversation_id"), table_name="chat_messages")
    op.drop_constraint("fk_chat_messages_conversation_id", "chat_messages", type_="foreignkey")
    op.drop_column("chat_messages", "conversation_id")
    op.drop_index(op.f("ix_chat_conversations_user_id"), table_name="chat_conversations")
    op.drop_table("chat_conversations")
