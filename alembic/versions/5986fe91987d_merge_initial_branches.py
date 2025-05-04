"""merge initial branches

Revision ID: 5986fe91987d
Revises: abc12345def6, 9c9c126820ff
Create Date: 2025-05-03 23:18:15.669098

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5986fe91987d'
down_revision: Union[str, None] = ('abc12345def6', '9c9c126820ff')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
