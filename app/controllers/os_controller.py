from app.config.settings import ROOT_DIR
from app.controllers._base import auditar, limite_desconto, usuario_atual
from app.database.database import SessionLocal
from app.reports.os_pdf import gerar_pdf_os
from app.repositories.estoque_repository import EstoqueRepository, MovimentacaoEstoqueRepository
from app.repositories.os_repository import ItemOSRepository, OrdemServicoRepository
from app.repositories.seguranca_repository import ConfiguracaoRepository
from app.repositories.venda_repository import FinanceiroLancamentoRepository
from app.services.estoque_service import EstoqueService
from app.services.os_service import OrdemServicoService
from app.utils.sessao import requer_permissao


def _service(session) -> OrdemServicoService:
    estoque_service = EstoqueService(
        EstoqueRepository(session),
        MovimentacaoEstoqueRepository(session),
    )
    return OrdemServicoService(
        OrdemServicoRepository(session),
        ItemOSRepository(session),
        FinanceiroLancamentoRepository(session),
        estoque_service,
    )


class OrdemServicoController:
    @requer_permissao("os", "ver")
    def listar(self):
        with SessionLocal() as session:
            return _service(session).listar()

    @requer_permissao("os", "ver")
    def listar_itens(self, os_id: int):
        with SessionLocal() as session:
            return _service(session).listar_itens(os_id)

    @requer_permissao("os", "criar")
    def abrir_os(self, dados: dict, usuario_id: int | None = None):
        with SessionLocal() as session:
            dados = dict(dados)
            dados["usuario_id"] = usuario_atual(usuario_id)
            ordem = _service(session).abrir_os(dados)
            auditar(session, "os", "ABRIR", ordem.numero, ordem.id)
            session.commit()
            return ordem

    @requer_permissao("os", "criar")
    def adicionar_item(self, dados: dict):
        with SessionLocal() as session:
            item = _service(session).adicionar_item(
                os_id=int(dados["os_id"]),
                tipo=dados["tipo"],
                produto_id=dados.get("produto_id"),
                descricao=dados["descricao"],
                quantidade=dados["quantidade"],
                valor_unitario=dados["valor_unitario"],
            )
            auditar(session, "os", "ADICIONAR_ITEM", item.descricao, item.os_id)
            session.commit()
            return item

    @requer_permissao("os", "editar")
    def atualizar_item(self, item_id: int, quantidade, valor_unitario):
        with SessionLocal() as session:
            item = _service(session).atualizar_item(item_id, quantidade, valor_unitario)
            auditar(session, "os", "EDITAR_ITEM", f"item={item_id}", item.os_id)
            session.commit()
            return item

    @requer_permissao("os", "editar")
    def definir_desconto(self, os_id: int, desconto="", acrescimo=""):
        """Desconto/acrescimo em R$ ou %, respeitando o limite do perfil (administrador sem limite)."""
        with SessionLocal() as session:
            ordem, percentual = _service(session).definir_desconto(
                os_id, desconto, acrescimo, limite_desconto(session)
            )
            auditar(
                session,
                "os",
                "DESCONTO",
                f"{ordem.numero} desconto={ordem.desconto} ({percentual:.1f}%) acrescimo={ordem.acrescimo} total={ordem.valor_total}",
                ordem.id,
            )
            session.commit()
            return ordem

    @requer_permissao("os", "excluir")
    def remover_item(self, item_id: int) -> None:
        with SessionLocal() as session:
            _service(session).remover_item(item_id)
            auditar(session, "os", "REMOVER_ITEM", f"item={item_id}")
            session.commit()

    @requer_permissao("os", "editar")
    def finalizar_os(
        self,
        os_id: int,
        usuario_id: int | None = None,
        data_vencimento=None,
        parcelas: int = 1,
        forma_pagamento: str | None = None,
    ):
        with SessionLocal() as session:
            ordem = _service(session).finalizar_os(
                os_id, usuario_atual(usuario_id), data_vencimento, parcelas, forma_pagamento
            )
            auditar(session, "os", "FINALIZAR", f"{ordem.numero} total={ordem.valor_total}", ordem.id)
            session.commit()
            return ordem

    @requer_permissao("os", "excluir")
    def cancelar_os(self, os_id: int, motivo: str, usuario_id: int | None = None):
        with SessionLocal() as session:
            ordem = _service(session).cancelar_os(os_id, motivo, usuario_atual(usuario_id))
            auditar(session, "os", "CANCELAR", f"{ordem.numero}: {motivo}", ordem.id)
            session.commit()
            return ordem

    @requer_permissao("os", "ver")
    def imprimir_os(self, os_id: int):
        """Gera o PDF da OS em exports/os/ e retorna o caminho."""
        with SessionLocal() as session:
            ordem = OrdemServicoRepository(session).buscar_por_id(int(os_id))
            if ordem is None:
                raise ValueError("Ordem de servico nao encontrada.")
            empresa = ConfiguracaoRepository(session).buscar_por_chave("empresa.nome")
            arquivo = gerar_pdf_os(ordem, ROOT_DIR / "exports" / "os", empresa.valor if empresa and empresa.valor else "")
            auditar(session, "os", "IMPRIMIR", ordem.numero, ordem.id)
            session.commit()
            return arquivo
