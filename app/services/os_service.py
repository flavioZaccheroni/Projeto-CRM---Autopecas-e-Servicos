from datetime import date, datetime
from decimal import Decimal

from app.models.financeiro_lancamento import FinanceiroLancamento
from app.models.item_os import ItemOS
from app.models.ordem_servico import OrdemServico
from app.repositories.os_repository import ItemOSRepository, OrdemServicoRepository
from app.repositories.venda_repository import FinanceiroLancamentoRepository
from app.services.estoque_service import EstoqueService
from app.utils.validators import validar_obrigatorio


class OrdemServicoService:
    def __init__(
        self,
        os_repository: OrdemServicoRepository,
        item_repository: ItemOSRepository,
        financeiro_repository: FinanceiroLancamentoRepository,
        estoque_service: EstoqueService,
    ) -> None:
        self.os_repository = os_repository
        self.item_repository = item_repository
        self.financeiro_repository = financeiro_repository
        self.estoque_service = estoque_service

    def listar(self) -> list[OrdemServico]:
        return self.os_repository.listar()

    def abrir_os(self, dados: dict) -> OrdemServico:
        validar_obrigatorio(dados.get("cliente_id"), "Cliente")
        validar_obrigatorio(dados.get("veiculo_id"), "Veiculo")
        validar_obrigatorio(dados.get("numero"), "Numero")
        ordem = OrdemServico(
            cliente_id=int(dados["cliente_id"]),
            veiculo_id=int(dados["veiculo_id"]),
            numero=str(dados["numero"]).strip(),
            data_abertura=_parse_data_hora(dados.get("data_abertura")),
            status=dados.get("status") or "ABERTA",
            defeito_relatado=(dados.get("defeito_relatado") or "").strip(),
            diagnostico=(dados.get("diagnostico") or "").strip(),
            valor_total=Decimal("0"),
            usuario_id=dados.get("usuario_id"),
        )
        return self.os_repository.salvar(ordem)

    def adicionar_item(
        self,
        os_id: int,
        tipo: str,
        produto_id,
        descricao: str,
        quantidade,
        valor_unitario,
    ) -> ItemOS:
        ordem = self.os_repository.buscar_por_id(int(os_id))
        if ordem is None:
            raise ValueError("Ordem de servico nao encontrada.")
        if ordem.status == "FINALIZADA":
            raise ValueError("OS finalizada nao permite novos itens.")

        tipo_normalizado = str(tipo or "").strip().upper()
        if tipo_normalizado not in {"PECA", "SERVICO"}:
            raise ValueError("Tipo do item deve ser PECA ou SERVICO.")
        if tipo_normalizado == "PECA" and produto_id in (None, ""):
            raise ValueError("Item de peca precisa ter produto.")
        validar_obrigatorio(descricao, "Descricao")

        quantidade_decimal = Decimal(str(quantidade).replace(",", "."))
        valor_unitario_decimal = Decimal(str(valor_unitario).replace(",", "."))
        if quantidade_decimal <= 0 or valor_unitario_decimal < 0:
            raise ValueError("Quantidade e valor unitario invalidos.")

        item = ItemOS(
            os_id=ordem.id,
            tipo=tipo_normalizado,
            produto_id=int(produto_id) if produto_id not in (None, "") else None,
            descricao=str(descricao).strip(),
            quantidade=quantidade_decimal,
            valor_unitario=valor_unitario_decimal,
            valor_total=quantidade_decimal * valor_unitario_decimal,
        )
        self.item_repository.salvar(item)
        ordem.valor_total = Decimal(ordem.valor_total or 0) + item.valor_total
        return item

    def finalizar_os(self, os_id: int, usuario_id: int | None = None, data_vencimento=None) -> OrdemServico:
        ordem = self.os_repository.buscar_por_id(int(os_id))
        if ordem is None:
            raise ValueError("Ordem de servico nao encontrada.")
        if not ordem.itens:
            raise ValueError("OS precisa ter pelo menos um item para finalizacao.")
        if ordem.status == "FINALIZADA":
            raise ValueError("OS ja finalizada.")

        for item in ordem.itens:
            if item.tipo == "PECA":
                self.estoque_service.movimentar(
                    produto_id=item.produto_id,
                    tipo="SAIDA",
                    quantidade=item.quantidade,
                    origem=f"OS:{ordem.numero}",
                    usuario_id=usuario_id or ordem.usuario_id,
                )

        ordem.status = "FINALIZADA"
        lancamento = FinanceiroLancamento(
            tipo="RECEBER",
            origem="OS",
            origem_id=ordem.id,
            cliente_id=ordem.cliente_id,
            fornecedor_id=None,
            descricao=f"Ordem de servico {ordem.numero}",
            valor=ordem.valor_total,
            data_vencimento=_parse_data(data_vencimento),
            status="ABERTO",
        )
        self.financeiro_repository.salvar(lancamento)
        return ordem


def _parse_data_hora(valor) -> datetime:
    if isinstance(valor, datetime):
        return valor
    if not valor:
        return datetime.utcnow()
    return datetime.fromisoformat(str(valor))


def _parse_data(valor) -> date:
    if isinstance(valor, date):
        return valor
    if not valor:
        return date.today()
    return date.fromisoformat(str(valor))
