"""allow several specialists per topic

Revision ID: 20260530_0004
Revises: 20260423_0003
Create Date: 2026-05-30

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20260530_0004'
down_revision: Union[str, None] = '20260423_0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'topic_specialists',
        sa.Column('topic_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('topic_id', 'user_id'),
    )
    op.execute(
        """
        INSERT INTO topic_specialists (topic_id, user_id)
        SELECT id, specialist_id
        FROM topics
        WHERE specialist_id IS NOT NULL
        """
    )


def downgrade() -> None:
    op.execute('DROP TABLE IF EXISTS topic_specialists')
