import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.database import Base
from app.models import (  # noqa: F401
    Auditoria,
    CaixaMovimentacao,
    CategoriaProduto,
    Cliente,
    Compra,
    Configuracao,
    Estoque,
    FinanceiroLancamento,
    Fornecedor,
    ItemCompra,
    ItemOS,
    ItemVenda,
    MarcaProduto,
    MovimentacaoEstoque,
    OrdemServico,
    Perfil,
    Permissao,
    Produto,
    Sequencia,
    Usuario,
    Veiculo,
    Venda,
)


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, future=True)
    with Session() as db_session:
        yield db_session


@pytest.fixture()
def app_db(tmp_path, monkeypatch):
    """Banco SQLite em arquivo + SessionLocal apontando para ele em todos os controllers.

    Permite testar controllers de ponta a ponta (permissoes, auditoria, commit) sem tocar no banco real.
    """
    import sys

    from app.database import database
    from app.database.alembic_runner import upgrade_to_head
    from app.database.init_db import initialize_database
    from app.utils.sessao import Sessao

    engine = create_engine(f"sqlite:///{tmp_path / 'teste.db'}", connect_args={"check_same_thread": False}, future=True)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setattr(database, "SessionLocal", factory)
    for nome, modulo in list(sys.modules.items()):
        if nome.startswith("app.") and hasattr(modulo, "SessionLocal"):
            monkeypatch.setattr(modulo, "SessionLocal", factory)
    database.importar_modelos()
    upgrade_to_head(engine)
    initialize_database()
    Sessao.encerrar()
    yield factory
    Sessao.encerrar()


# Widgets Qt criados nos testes ficam vivos ate o fim do processo: destrui-los em Python enquanto sinais
# ainda apontam para eles derruba o Qt (segfault intermitente, exit 139, que reprovava o CI).
_VIVOS: list = []


def _manter_widgets_vivos() -> None:
    try:
        from PySide6.QtWidgets import QWidget
    except ImportError:
        return
    original = QWidget.__init__

    def __init__(self, *args, **kwargs):
        original(self, *args, **kwargs)
        _VIVOS.append(self)

    QWidget.__init__ = __init__


_manter_widgets_vivos()
