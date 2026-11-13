"""Catalogo de servicos e mecanico responsavel na OS.

Revision ID: 0003
Revises: 0002
"""
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.database.database import Base, importar_modelos
    from app.database.migrations import aplicar_migracoes

    importar_modelos()
    conn = op.get_bind()
    Base.metadata.create_all(bind=conn)  # cria a tabela servicos se ainda nao existe
    aplicar_migracoes(conn)  # adiciona ordens_servico.mecanico


def downgrade() -> None:
    raise NotImplementedError("Reversao nao suportada.")
