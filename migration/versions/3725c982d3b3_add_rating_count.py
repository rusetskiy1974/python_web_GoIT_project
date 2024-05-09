"""Add rating count

Revision ID: 3725c982d3b3
Revises: 3a0579407bb2
Create Date: 2024-05-09 08:28:24.954324

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3725c982d3b3'
down_revision: Union[str, None] = '3a0579407bb2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('images', sa.Column('rating_count', sa.Integer(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('images', 'rating_count')
    # ### end Alembic commands ###
