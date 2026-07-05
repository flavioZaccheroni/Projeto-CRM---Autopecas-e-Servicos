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


class CrudController:
    def __init__(self, repository_cls, service_cls) -> None:
        self.repository_cls = repository_cls
        self.service_cls = service_cls

    def listar(self):
        with SessionLocal() as session:
            return self.service_cls(self.repository_cls(session)).listar()

    def salvar(self, dados: dict):
        with SessionLocal() as session:
            item = self.service_cls(self.repository_cls(session)).salvar(dados)
            session.commit()
            return item


class ClienteController(CrudController):
    def __init__(self) -> None:
        super().__init__(ClienteRepository, ClienteService)


class VeiculoController(CrudController):
    def __init__(self) -> None:
        super().__init__(VeiculoRepository, VeiculoService)


class FornecedorController(CrudController):
    def __init__(self) -> None:
        super().__init__(FornecedorRepository, FornecedorService)


class CategoriaProdutoController(CrudController):
    def __init__(self) -> None:
        super().__init__(CategoriaProdutoRepository, CategoriaProdutoService)


class MarcaProdutoController(CrudController):
    def __init__(self) -> None:
        super().__init__(MarcaProdutoRepository, MarcaProdutoService)


class ProdutoController(CrudController):
    def __init__(self) -> None:
        super().__init__(ProdutoRepository, ProdutoService)
