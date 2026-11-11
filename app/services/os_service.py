from decimal import Decimal

from app.models.item_os import ItemOS
from app.models.ordem_servico import OrdemServico
from app.repositories.os_repository import ItemOSRepository, OrdemServicoRepository
from app.repositories.venda_repository import FinanceiroLancamentoRepository
from app.services._itens import recalcular_total
from app.services.estoque_service import EstoqueService
from app.services.financeiro_service import cancelar_lancamentos_origem, gerar_lancamentos
from app.services.numeracao_service import NumeracaoService
from app.services.venda_service import _forma_pagamento
from app.utils.datas import parse_data_hora
from app.utils.numeros import para_decimal
from app.utils.validators import validar_obrigatorio


STATUS_ABERTOS = {"ABERTA", "EM_ANDAMENTO", "AGUARDANDO_PECA", "AGUARDANDO_APROVACAO"}


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

    @property
    def _session(self):
        return self.os_repository.session

    def listar(self) -> list[OrdemServico]:
        return self.os_repository.listar()

    def abrir_os(self, dados: dict) -> OrdemServico:
        validar_obrigatorio(dados.get("cliente_id"), "Cliente")
        validar_obrigatorio(dados.get("veiculo_id"), "Veiculo")
        numero = str(dados.get("numero") or "").strip() or NumeracaoService(self._session).proximo("OS")
        ordem = OrdemServico(
            cliente_id=int(dados["cliente_id"]),
            veiculo_id=int(dados["veiculo_id"]),
            numero=numero,
            data_abertura=parse_data_hora(dados.get("data_abertura")),
            status=dados.get("status") or "ABERTA",
            defeito_relatado=(dados.get("defeito_relatado") or "").strip(),
            diagnostico=(dados.get("diagnostico") or "").strip(),
            valor_total=Decimal("0"),
            usuario_id=dados.get("usuario_id"),
        )
        return self.os_repository.salvar(ordem)

    # -- itens ------------------------------------------------------------------------------
    def adicionar_item(
        self,
        os_id: int,
        tipo: str,
        produto_id,
        descricao: str,
        quantidade,
        valor_unitario,
    ) -> ItemOS:
        ordem = self._obter_editavel(os_id)
        tipo_normalizado, produto, descricao_limpa, quantidade_decimal, valor_decimal = self._validar_item(
            tipo, produto_id, descricao, quantidade, valor_unitario
        )
        item = ItemOS(
            os_id=ordem.id,
            tipo=tipo_normalizado,
            produto_id=produto,
            descricao=descricao_limpa,
            quantidade=quantidade_decimal,
            valor_unitario=valor_decimal,
            valor_total=quantidade_decimal * valor_decimal,
        )
        self.item_repository.salvar(item)
        ordem.valor_total = Decimal(ordem.valor_total or 0) + item.valor_total
        return item

    def atualizar_item(self, item_id: int, quantidade, valor_unitario) -> ItemOS:
        item = self._obter_item(item_id)
        ordem = self._obter_editavel(item.os_id)
        quantidade_decimal = para_decimal(quantidade, "Quantidade")
        valor_decimal = para_decimal(valor_unitario, "Valor unitario")
        if quantidade_decimal <= 0 or valor_decimal < 0:
            raise ValueError("Quantidade e valor unitario invalidos.")
        item.quantidade = quantidade_decimal
        item.valor_unitario = valor_decimal
        item.valor_total = quantidade_decimal * valor_decimal
        self.item_repository.salvar(item)
        recalcular_total(self._session, ordem)
        return item

    def remover_item(self, item_id: int) -> None:
        item = self._obter_item(item_id)
        ordem = self._obter_editavel(item.os_id)
        self.item_repository.excluir(item)
        recalcular_total(self._session, ordem)

    # -- ciclo de vida ----------------------------------------------------------------------
    def finalizar_os(
        self,
        os_id: int,
        usuario_id: int | None = None,
        data_vencimento=None,
        parcelas: int = 1,
        forma_pagamento: str | None = None,
    ) -> OrdemServico:
        ordem = self._obter(os_id)
        if ordem.status == "FINALIZADA":
            raise ValueError("OS ja finalizada.")
        if ordem.status not in STATUS_ABERTOS:
            raise ValueError(f"OS {ordem.status.lower()} nao pode ser finalizada.")
        if not ordem.itens:
            raise ValueError("OS precisa ter pelo menos um item para finalizacao.")
        forma = _forma_pagamento(forma_pagamento)

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
        ordem.forma_pagamento = forma
        ordem.parcelas = (1 if parcelas in (None, "") else int(parcelas))
        gerar_lancamentos(
            self.financeiro_repository,
            tipo="RECEBER",
            origem="OS",
            origem_id=ordem.id,
            descricao=f"Ordem de servico {ordem.numero}",
            valor=ordem.valor_total,
            parcelas=ordem.parcelas,
            primeiro_vencimento=data_vencimento,
            cliente_id=ordem.cliente_id,
        )
        return ordem

    def cancelar_os(self, os_id: int, motivo: str, usuario_id: int | None = None) -> OrdemServico:
        ordem = self._obter(os_id)
        if ordem.status == "CANCELADA":
            raise ValueError("OS ja cancelada.")
        validar_obrigatorio(motivo, "Motivo do cancelamento")

        if ordem.status == "FINALIZADA":
            for item in ordem.itens:
                if item.tipo == "PECA":
                    self.estoque_service.movimentar(
                        produto_id=item.produto_id,
                        tipo="ENTRADA",
                        quantidade=item.quantidade,
                        origem=f"CANCELAMENTO OS:{ordem.numero}",
                        usuario_id=usuario_id or ordem.usuario_id,
                    )
            cancelar_lancamentos_origem(self._session, "OS", ordem.id, usuario_id)
        ordem.status = "CANCELADA"
        ordem.motivo_cancelamento = motivo.strip()
        return ordem

    # -- internos ---------------------------------------------------------------------------
    def _obter(self, os_id: int) -> OrdemServico:
        ordem = self.os_repository.buscar_por_id(int(os_id))
        if ordem is None:
            raise ValueError("Ordem de servico nao encontrada.")
        return ordem

    def _obter_editavel(self, os_id: int) -> OrdemServico:
        ordem = self._obter(os_id)
        if ordem.status not in STATUS_ABERTOS:
            raise ValueError(f"OS {ordem.status.lower()} nao permite alterar itens.")
        return ordem

    def _obter_item(self, item_id: int) -> ItemOS:
        item = self.item_repository.buscar_por_id(int(item_id))
        if item is None:
            raise ValueError("Item nao encontrado.")
        return item

    @staticmethod
    def _validar_item(tipo, produto_id, descricao, quantidade, valor_unitario):
        tipo_normalizado = str(tipo or "").strip().upper()
        if tipo_normalizado not in {"PECA", "SERVICO"}:
            raise ValueError("Tipo do item deve ser PECA ou SERVICO.")
        if tipo_normalizado == "PECA" and produto_id in (None, ""):
            raise ValueError("Item de peca precisa ter produto.")
        validar_obrigatorio(descricao, "Descricao")
        quantidade_decimal = para_decimal(quantidade, "Quantidade")
        valor_decimal = para_decimal(valor_unitario, "Valor unitario")
        if quantidade_decimal <= 0 or valor_decimal < 0:
            raise ValueError("Quantidade e valor unitario invalidos.")
        produto = int(produto_id) if produto_id not in (None, "") else None
        return tipo_normalizado, produto, str(descricao).strip(), quantidade_decimal, valor_decimal
