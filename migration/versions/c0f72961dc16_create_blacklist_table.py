"""create blacklist table

Revision ID: c0f72961dc16
Revises: 197fda1bbd91
Create Date: 2024-05-05 02:21:57.379779

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c0f72961dc16'
down_revision: Union[str, None] = '197fda1bbd91'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'black_list',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('token', sa.String(255), unique=True, index=True),
        sa.Column('email', sa.String(320), unique=True, index=True, nullable=False)
    )


def downgrade() -> None:
    op.drop_table('black_list')
