"""fix_id_tag

Revision ID: 197fda1bbd91
Revises: a2cca2e207e5
Create Date: 2024-04-27 10:05:07.675451

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '197fda1bbd91'
down_revision: Union[str, None] = 'a2cca2e207e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
