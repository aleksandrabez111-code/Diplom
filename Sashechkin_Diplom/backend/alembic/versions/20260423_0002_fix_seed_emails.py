"""fix invalid demo emails

Revision ID: 20260423_0002
Revises: 20260423_0001
Create Date: 2026-04-23

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '20260423_0002'
down_revision: Union[str, None] = '20260423_0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE users
        SET email = REPLACE(email, '@tfoms.local', '@tfoms.example.com')
        WHERE email LIKE '%@tfoms.local'
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE users
        SET email = REPLACE(email, '@tfoms.example.com', '@tfoms.local')
        WHERE email LIKE '%@tfoms.example.com'
        """
    )
