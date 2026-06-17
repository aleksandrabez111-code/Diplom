"""simplify schema for diploma mvp

Revision ID: 20260423_0003
Revises: 20260423_0002
Create Date: 2026-04-23

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20260423_0003'
down_revision: Union[str, None] = '20260423_0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


user_role = sa.Enum('admin', 'specialist', name='userrole')
ticket_status = sa.Enum('new', 'in_progress', 'closed', name='ticketstatus')


def upgrade() -> None:
    bind = op.get_bind()

    op.execute('DROP TABLE IF EXISTS ticket_actions')
    op.execute('DROP TABLE IF EXISTS topic_specialists')
    op.execute('DROP TABLE IF EXISTS tickets')
    op.execute('DROP TABLE IF EXISTS topics')
    op.execute('DROP TABLE IF EXISTS users')

    user_role.create(bind, checkfirst=True)
    ticket_status.create(bind, checkfirst=True)

    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=64), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('role', user_role, nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email'),
    )
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    op.create_table(
        'topics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('specialist_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['specialist_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    op.create_table(
        'tickets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ticket_number', sa.String(length=32), nullable=False),
        sa.Column('topic_id', sa.Integer(), nullable=False),
        sa.Column('message_text', sa.Text(), nullable=False),
        sa.Column('contact_email', sa.String(length=255), nullable=False),
        sa.Column('status', ticket_status, nullable=False),
        sa.Column('assigned_specialist_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id']),
        sa.ForeignKeyConstraint(['assigned_specialist_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ticket_number'),
    )
    op.create_index(op.f('ix_tickets_ticket_number'), 'tickets', ['ticket_number'], unique=True)
    op.create_index(op.f('ix_tickets_topic_id'), 'tickets', ['topic_id'], unique=False)
    op.create_index(op.f('ix_tickets_assigned_specialist_id'), 'tickets', ['assigned_specialist_id'], unique=False)


def downgrade() -> None:
    op.execute('DROP TABLE IF EXISTS tickets')
    op.execute('DROP TABLE IF EXISTS topics')
    op.execute('DROP TABLE IF EXISTS users')

    bind = op.get_bind()
    ticket_status.drop(bind, checkfirst=True)
    user_role.drop(bind, checkfirst=True)
