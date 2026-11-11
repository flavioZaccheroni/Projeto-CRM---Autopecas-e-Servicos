"""Migrador minimo e idempotente para bancos criados antes das Sprints 1 e 2.

`create_all` cria tabelas novas, mas nao altera tabelas existentes. Este modulo adiciona as
colunas novas quando elas ainda nao existem, sem apagar nenhum dado. Sera substituido por
Alembic em uma etapa futura.
"""

import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


logger = logging.getLogger(__name__)

# tabela -> [(coluna, DDL)]
COLUNAS_NOVAS: dict[str, list[tuple[str, str]]] = {
    "usuarios": [
        ("precisa_trocar_senha", "BOOLEAN NOT NULL DEFAULT 0"),
        ("tentativas_falhas", "INTEGER NOT NULL DEFAULT 0"),
        ("bloqueado_ate", "DATETIME"),
    ],
    "vendas": [
        ("forma_pagamento", "VARCHAR(30)"),
        ("parcelas", "INTEGER NOT NULL DEFAULT 1"),
        ("motivo_cancelamento", "VARCHAR(255)"),
    ],
    "ordens_servico": [
        ("forma_pagamento", "VARCHAR(30)"),
        ("parcelas", "INTEGER NOT NULL DEFAULT 1"),
        ("motivo_cancelamento", "VARCHAR(255)"),
    ],
    "compras": [
        ("motivo_cancelamento", "VARCHAR(255)"),
    ],
}


def aplicar_migracoes(engine: Engine) -> list[str]:
    """Adiciona colunas ausentes. Retorna a lista de colunas criadas (vazia se nada mudou)."""
    criadas: list[str] = []
    inspector = inspect(engine)
    tabelas = set(inspector.get_table_names())
    with engine.begin() as conn:
        for tabela, colunas in COLUNAS_NOVAS.items():
            if tabela not in tabelas:
                continue
            existentes = {coluna["name"] for coluna in inspector.get_columns(tabela)}
            for nome, ddl in colunas:
                if nome not in existentes:
                    conn.execute(text(f"ALTER TABLE {tabela} ADD COLUMN {nome} {ddl}"))
                    criadas.append(f"{tabela}.{nome}")
    if criadas:
        logger.info("Migracao aplicou colunas: %s", ", ".join(criadas))
    return criadas
