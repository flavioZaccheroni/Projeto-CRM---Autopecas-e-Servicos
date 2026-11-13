from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.categoria_produto import CategoriaProduto
from app.models.cliente import Cliente
from app.models.fornecedor import Fornecedor
from app.models.marca_produto import MarcaProduto
from app.models.produto import Produto
from app.models.servico import Servico
from app.models.veiculo import Veiculo
from app.repositories.base_repository import BaseRepository


class ClienteRepository(BaseRepository[Cliente]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Cliente)

    def buscar_por_cpf_cnpj(self, cpf_cnpj: str) -> Cliente | None:
        return self.session.scalar(select(Cliente).where(Cliente.cpf_cnpj == cpf_cnpj))


class VeiculoRepository(BaseRepository[Veiculo]):
    eager_load = ('cliente',)

    def __init__(self, session: Session) -> None:
        super().__init__(session, Veiculo)

    def buscar_por_placa(self, placa: str) -> Veiculo | None:
        return self.session.scalar(select(Veiculo).where(Veiculo.placa == placa))


class ServicoRepository(BaseRepository[Servico]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Servico)

    def buscar_por_nome(self, nome: str) -> Servico | None:
        return self.session.scalar(select(Servico).where(Servico.nome == nome))


class FornecedorRepository(BaseRepository[Fornecedor]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Fornecedor)

    def buscar_por_cnpj(self, cnpj: str) -> Fornecedor | None:
        return self.session.scalar(select(Fornecedor).where(Fornecedor.cnpj == cnpj))


class CategoriaProdutoRepository(BaseRepository[CategoriaProduto]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, CategoriaProduto)

    def buscar_por_nome(self, nome: str) -> CategoriaProduto | None:
        return self.session.scalar(select(CategoriaProduto).where(CategoriaProduto.nome == nome))


class MarcaProdutoRepository(BaseRepository[MarcaProduto]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, MarcaProduto)

    def buscar_por_nome(self, nome: str) -> MarcaProduto | None:
        return self.session.scalar(select(MarcaProduto).where(MarcaProduto.nome == nome))


class ProdutoRepository(BaseRepository[Produto]):
    eager_load = ('categoria', 'marca')

    def __init__(self, session: Session) -> None:
        super().__init__(session, Produto)

    def buscar_por_codigo(self, codigo: str) -> Produto | None:
        return self.session.scalar(select(Produto).where(Produto.codigo == codigo))
