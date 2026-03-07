"""merge_heads_temp_mailbox_lifecycle

Revision ID: 2f4b8d7c6a11
Revises: 1c9e6f4a2b31, e7f8a9b0c1d2
Create Date: 2026-03-07 19:35:00.000000
"""
from typing import Sequence, Union


revision: str = "2f4b8d7c6a11"
down_revision: Union[str, Sequence[str], None] = ("1c9e6f4a2b31", "e7f8a9b0c1d2")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # merge revision, no-op
    pass


def downgrade() -> None:
    # merge revision, no-op
    pass
