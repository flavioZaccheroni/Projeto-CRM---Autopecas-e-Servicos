from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config.settings import DATA_DIR, DATABASE_URL

DATA_DIR.mkdir(parents=True, exist_ok=True)


class Base(DeclarativeBase):
    pass


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    future=True,
)


def importar_modelos() -> None:
    """Registra todos os modelos em Base.metadata (necessario antes de create_all/Alembic)."""
    from app.models import (  # noqa: F401
        auditoria,
        caixa_movimentacao,
        categoria_produto,
        cliente,
        compra,
        configuracao,
        estoque,
        financeiro_lancamento,
        fornecedor,
        item_compra,
        item_os,
        item_venda,
        marca_produto,
        movimentacao_estoque,
        ordem_servico,
        perfil,
        permissao,
        produto,
        sequencia,
        usuario,
        veiculo,
        venda,
    )


def create_database() -> None:
    """Cria/atualiza o schema aplicando as migracoes do Alembic ate a versao mais recente."""
    from app.database.alembic_runner import upgrade_to_head

    importar_modelos()
    upgrade_to_head(engine)
