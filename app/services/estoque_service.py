from datetime import datetime
from decimal import Decimal

from app.models.estoque import Estoque
from app.models.movimentacao_estoque import MovimentacaoEstoque
from app.repositories.estoque_repository import EstoqueRepository, MovimentacaoEstoqueRepository
from app.utils.validators import validar_obrigatorio


class EstoqueService:
    def __init__(
        self,
        estoque_repository: EstoqueRepository,
        movimentacao_repository: MovimentacaoEstoqueRepository,
    ) -> None:
        self.estoque_repository = estoque_repository
        self.movimentacao_repository = movimentacao_repository

    def listar(self) -> list[Estoque]:
        return self.estoque_repository.listar()

    def listar_movimentacoes(self) -> list[MovimentacaoEstoque]:
        return self.movimentacao_repository.listar()

    def movimentar(
        self,
        produto_id: int,
        tipo: str,
        quantidade,
        origem: str,
        usuario_id: int | None = None,
        localizacao: str | None = None,
    ) -> MovimentacaoEstoque:
        validar_obrigatorio(produto_id, "Produto")
        validar_obrigatorio(tipo, "Tipo")
        validar_obrigatorio(origem, "Origem")
        quantidade_decimal = Decimal(str(quantidade).replace(",", "."))
        if quantidade_decimal <= 0:
            raise ValueError("Quantidade deve ser maior que zero.")

        estoque = self.estoque_repository.buscar_por_produto(int(produto_id))
        if estoque is None:
            estoque = Estoque(produto_id=int(produto_id), quantidade_atual=Decimal("0"), localizacao=localizacao)
            self.estoque_repository.salvar(estoque)

        saldo_anterior = Decimal(estoque.quantidade_atual)
        tipo_normalizado = tipo.upper()
        if tipo_normalizado == "ENTRADA":
            saldo_posterior = saldo_anterior + quantidade_decimal
        elif tipo_normalizado == "SAIDA":
            saldo_posterior = saldo_anterior - quantidade_decimal
            if saldo_posterior < 0:
                raise ValueError("Estoque insuficiente para saida.")
        elif tipo_normalizado == "AJUSTE":
            saldo_posterior = quantidade_decimal
        else:
            raise ValueError("Tipo de movimento deve ser ENTRADA, SAIDA ou AJUSTE.")

        estoque.quantidade_atual = saldo_posterior
        estoque.localizacao = localizacao or estoque.localizacao
        estoque.atualizado_em = datetime.utcnow()
        movimento = MovimentacaoEstoque(
            produto_id=int(produto_id),
            tipo=tipo_normalizado,
            origem=origem,
            quantidade=quantidade_decimal,
            saldo_anterior=saldo_anterior,
            saldo_posterior=saldo_posterior,
            usuario_id=usuario_id,
        )
        self.movimentacao_repository.salvar(movimento)
        return movimento
