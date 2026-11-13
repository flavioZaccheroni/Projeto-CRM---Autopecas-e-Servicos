"""Desconto e acrescimo em vendas e ordens de servico.

Revision ID: 0002
Revises: 0001
"""
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.database.migrations import aplicar_migracoes

    aplicar_migracoes(op.get_bind())  # idempotente: so adiciona o que falta


def downgrade() -> None:
    raise NotImplementedError("Reversao nao suportada.")
