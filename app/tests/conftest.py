import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.database import Base
from app.models import (  # noqa: F401
    CategoriaProduto,
    CaixaMovimentacao,
    Cliente,
    Compra,
    Estoque,
    Fornecedor,
    FinanceiroLancamento,
    ItemCompra,
    ItemOS,
    ItemVenda,
    MarcaProduto,
    MovimentacaoEstoque,
    OrdemServico,
    Perfil,
    Permissao,
    Produto,
    Usuario,
    Venda,
    Veiculo,
)


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, future=True)
    with Session() as db_session:
        yield db_session
