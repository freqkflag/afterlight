"""initial schema

Revision ID: b0839e05bdf7
Revises:
Create Date: 2026-10-20 08:02:57.655368
"""

from typing import Sequence, Union

from alembic import op

from app.database import Base
from app.models import *  # noqa: F401,F403

revision: str = "b0839e05bdf7"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
