"""empty message

Revision ID: 8004cf85d029
Revises: b9dcbafaea35
Create Date: 2025-10-28 15:57:32.949387

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8004cf85d029"
down_revision: Union[str, Sequence[str], None] = "b9dcbafaea35"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
