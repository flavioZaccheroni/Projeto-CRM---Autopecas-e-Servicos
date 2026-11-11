from app.controllers._base import auditar
from app.database.database import SessionLocal
from app.repositories.cadastro_repository import (
    CategoriaProdutoRepository,
    ClienteRepository,
    FornecedorRepository,
    MarcaProdutoRepository,
    ProdutoRepository,
    VeiculoRepository,
)
from app.services.cadastro_service import (
    CategoriaProdutoService,
    ClienteService,
    FornecedorService,
    MarcaProdutoService,
    ProdutoService,
    VeiculoService,
)
from app.utils.sessao import Sessao


class CrudController:
    modulo = ""

    def __init__(self, repository_cls, service_cls) -> None:
        self.repository_cls = repository_cls
        self.service_cls = service_cls

    def listar(self):
        Sessao.exigir(self.modulo, "ver")
        with SessionLocal() as session:
            return self.service_cls(self.repository_cls(session)).listar()

    def salvar(self, dados: dict):
        editando = dados.get("id") not in (None, "")
        Sessao.exigir(self.modulo, "editar" if editando else "criar")
        with SessionLocal() as session:
            item = self.service_cls(self.repository_cls(session)).salvar(dados)
            auditar(session, self.modulo, "EDITAR" if editando else "CRIAR", str(item), item.id)
            session.commit()
            return item


class ClienteController(CrudController):
    modulo = "clientes"

    def __init__(self) -> None:
        super().__init__(ClienteRepository, ClienteService)


class VeiculoController(CrudController):
    modulo = "veiculos"

    def __init__(self) -> None:
        super().__init__(VeiculoRepository, VeiculoService)


class FornecedorController(CrudController):
    modulo = "fornecedores"

    def __init__(self) -> None:
        super().__init__(FornecedorRepository, FornecedorService)


class CategoriaProdutoController(CrudController):
    modulo = "categorias"

    def __init__(self) -> None:
        super().__init__(CategoriaProdutoRepository, CategoriaProdutoService)


class MarcaProdutoController(CrudController):
    modulo = "marcas"

    def __init__(self) -> None:
        super().__init__(MarcaProdutoRepository, MarcaProdutoService)


class ProdutoController(CrudController):
    modulo = "produtos"

    def __init__(self) -> None:
        super().__init__(ProdutoRepository, ProdutoService)
