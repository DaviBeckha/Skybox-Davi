"""initial — demos, matches, players, rounds

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-25

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "demos",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("filename", sa.Text(), nullable=False),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("parsed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
    )
    op.create_table(
        "matches",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("demo_id", sa.Uuid(), sa.ForeignKey("demos.id"), nullable=False),
        sa.Column("map", sa.Text(), nullable=False),
        sa.Column("team_a", sa.Text(), nullable=True),
        sa.Column("team_b", sa.Text(), nullable=True),
        sa.Column("score_a", sa.Integer(), nullable=True),
        sa.Column("score_b", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tick_rate", sa.Integer(), nullable=True),
    )
    op.create_table(
        "players",
        sa.Column("match_id", sa.Uuid(), sa.ForeignKey("matches.id"), nullable=False),
        sa.Column("steam_id", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("team", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("match_id", "steam_id"),
    )
    op.create_table(
        "rounds",
        sa.Column("match_id", sa.Uuid(), sa.ForeignKey("matches.id"), nullable=False),
        sa.Column("round_number", sa.Integer(), nullable=False),
        sa.Column("winner", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("start_tick", sa.BigInteger(), nullable=True),
        sa.Column("end_tick", sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint("match_id", "round_number"),
    )


def downgrade() -> None:
    op.drop_table("rounds")
    op.drop_table("players")
    op.drop_table("matches")
    op.drop_table("demos")
