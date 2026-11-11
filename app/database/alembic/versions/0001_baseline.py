"""Migracao base: cria o schema completo e atualiza bancos anteriores ao Alembic.

Revision ID: 0001
Revises:
"""
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.database.database import Base, importar_modelos
    from app.database.migrations import aplicar_migracoes

    importar_modelos()
    conn = op.get_bind()
    Base.metadata.create_all(bind=conn)  # checkfirst: so cria o que falta
    aplicar_migracoes(conn)  # bancos antigos: adiciona colunas novas sem perder dados


def downgrade() -> None:
    raise NotImplementedError("A migracao base nao pode ser revertida.")
