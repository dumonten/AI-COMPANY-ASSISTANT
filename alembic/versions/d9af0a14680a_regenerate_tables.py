"""Regenerate tables

Revision ID: d9af0a14680a
Revises: 8b1a0afdecf3
Create Date: 2024-05-16 04:11:20.262115

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd9af0a14680a'
down_revision: Union[str, None] = '8b1a0afdecf3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('company_company_name_key', 'company', type_='unique')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint('company_company_name_key', 'company', ['company_name'])
    # ### end Alembic commands ###
