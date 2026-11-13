from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.categoria_produto import CategoriaProduto
from app.models.cliente import Cliente
from app.models.fornecedor import Fornecedor
from app.models.marca_produto import MarcaProduto
from app.models.produto import Produto
from app.models.servico import Servico
from app.models.veiculo import Veiculo


class LookupService:
    """Listas (id, rotulo, extra) para os seletores das telas. Apenas ativos, em ordem alfabetica."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def clientes(self) -> list[tuple[int, str, str]]:
        linhas = self.session.execute(
            select(Cliente.id, Cliente.nome, Cliente.cpf_cnpj).where(Cliente.ativo.is_(True)).order_by(Cliente.nome)
        )
        return [(i, nome, cpf or "") for i, nome, cpf in linhas]

    def fornecedores(self) -> list[tuple[int, str, str]]:
        linhas = self.session.execute(
            select(Fornecedor.id, Fornecedor.razao_social, Fornecedor.cnpj).where(Fornecedor.ativo.is_(True)).order_by(Fornecedor.razao_social)
        )
        return [(i, nome, cnpj or "") for i, nome, cnpj in linhas]

    def produtos(self) -> list[tuple[int, str, str]]:
        """extra = preco de venda (usado para preencher o valor unitario)."""
        linhas = self.session.execute(
            select(Produto.id, Produto.codigo, Produto.descricao, Produto.preco_venda)
            .where(Produto.ativo.is_(True))
            .order_by(Produto.descricao)
        )
        return [(i, f"{codigo} - {descricao}", str(preco)) for i, codigo, descricao, preco in linhas]

    def veiculos(self, cliente_id: int | None = None) -> list[tuple[int, str, str]]:
        consulta = select(Veiculo.id, Veiculo.placa, Veiculo.marca, Veiculo.modelo, Veiculo.cliente_id).order_by(Veiculo.placa)
        if cliente_id:
            consulta = consulta.where(Veiculo.cliente_id == int(cliente_id))
        return [
            (i, f"{placa} - {' '.join(p for p in (marca, modelo) if p)}".rstrip(" -"), str(cid))
            for i, placa, marca, modelo, cid in self.session.execute(consulta)
        ]

    def categorias(self) -> list[tuple[int, str, str]]:
        linhas = self.session.execute(select(CategoriaProduto.id, CategoriaProduto.nome).where(CategoriaProduto.ativo.is_(True)).order_by(CategoriaProduto.nome))
        return [(i, nome, "") for i, nome in linhas]

    def marcas(self) -> list[tuple[int, str, str]]:
        linhas = self.session.execute(select(MarcaProduto.id, MarcaProduto.nome).where(MarcaProduto.ativo.is_(True)).order_by(MarcaProduto.nome))
        return [(i, nome, "") for i, nome in linhas]

    def servicos(self) -> list[tuple[int, str, str]]:
        """extra = preco padrao (usado para preencher o valor unitario da OS)."""
        linhas = self.session.execute(select(Servico.id, Servico.nome, Servico.preco_padrao).where(Servico.ativo.is_(True)).order_by(Servico.nome))
        return [(i, nome, str(preco)) for i, nome, preco in linhas]
