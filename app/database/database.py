from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config.settings import DATABASE_URL, DATA_DIR


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


def create_database() -> None:
    from app.models import (  # noqa: F401
        categoria_produto,
        cliente,
        compra,
        estoque,
        fornecedor,
        item_compra,
        marca_produto,
        movimentacao_estoque,
        perfil,
        permissao,
        produto,
        usuario,
        veiculo,
    )

    Base.metadata.create_all(bind=engine)
