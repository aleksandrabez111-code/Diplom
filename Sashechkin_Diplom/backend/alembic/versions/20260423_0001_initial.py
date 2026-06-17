"""initial schema

Revision ID: 20260423_0001
Revises:
Create Date: 2026-04-23

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20260423_0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


user_role = sa.Enum('admin', 'specialist', name='userrole')
ticket_status = sa.Enum('new', 'assigned', 'in_progress', 'closed', 'archived', name='ticketstatus')
action_type = sa.Enum(
    'created',
    'auto_assigned',
    'taken_in_work',
    'transferred',
    'status_changed',
    'closed',
    'archived',
    'unarchived',
    name='ticketactiontype',
)


def upgrade() -> None:
    bind = op.get_bind()
    user_role.create(bind, checkfirst=True)
    ticket_status.create(bind, checkfirst=True)
    action_type.create(bind, checkfirst=True)

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
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username'),
    )
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    op.create_table(
        'topics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    op.create_table(
        'topic_specialists',
        sa.Column('topic_id', sa.Integer(), nullable=False),
        sa.Column('specialist_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['specialist_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('topic_id', 'specialist_id'),
        sa.UniqueConstraint('topic_id', 'specialist_id', name='uq_topic_specialist'),
    )

    op.create_table(
        'tickets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ticket_number', sa.String(length=32), nullable=False),
        sa.Column('topic_id', sa.Integer(), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('contact_email', sa.String(length=255), nullable=False),
        sa.Column('status', ticket_status, nullable=False),
        sa.Column('assigned_specialist_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_from_ip', sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(['assigned_specialist_id'], ['users.id']),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ticket_number'),
    )
    op.create_index(op.f('ix_tickets_ticket_number'), 'tickets', ['ticket_number'], unique=True)
    op.create_index(op.f('ix_tickets_topic_id'), 'tickets', ['topic_id'], unique=False)
    op.create_index(op.f('ix_tickets_assigned_specialist_id'), 'tickets', ['assigned_specialist_id'], unique=False)

    op.create_table(
        'ticket_actions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ticket_id', sa.Integer(), nullable=False),
        sa.Column('action_type', action_type, nullable=False),
        sa.Column('performed_by_user_id', sa.Integer(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['performed_by_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_ticket_actions_action_type'), 'ticket_actions', ['action_type'], unique=False)
    op.create_index(op.f('ix_ticket_actions_ticket_id'), 'ticket_actions', ['ticket_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_ticket_actions_ticket_id'), table_name='ticket_actions')
    op.drop_index(op.f('ix_ticket_actions_action_type'), table_name='ticket_actions')
    op.drop_table('ticket_actions')

    op.drop_index(op.f('ix_tickets_assigned_specialist_id'), table_name='tickets')
    op.drop_index(op.f('ix_tickets_topic_id'), table_name='tickets')
    op.drop_index(op.f('ix_tickets_ticket_number'), table_name='tickets')
    op.drop_table('tickets')

    op.drop_table('topic_specialists')
    op.drop_table('topics')

    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_table('users')

    bind = op.get_bind()
    action_type.drop(bind, checkfirst=True)
    ticket_status.drop(bind, checkfirst=True)
    user_role.drop(bind, checkfirst=True)
