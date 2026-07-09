from zipfile import ZipFile

from app.models.cliente import Cliente
from app.models.venda import Venda
from app.repositories.base_repository import BaseRepository
from app.models.caixa_movimentacao import CaixaMovimentacao
from app.models.estoque import Estoque
from app.models.financeiro_lancamento import FinanceiroLancamento
from app.models.ordem_servico import OrdemServico
from app.services.relatorio_service import RelatorioService


def _service(session, tmp_path):
    return RelatorioService(
        BaseRepository(session, Venda),
        BaseRepository(session, Estoque),
        BaseRepository(session, OrdemServico),
        BaseRepository(session, FinanceiroLancamento),
        BaseRepository(session, CaixaMovimentacao),
        output_dir=tmp_path,
    )


def test_relatorio_vendas_exporta_pdf(session, tmp_path):
    cliente = Cliente(nome="Cliente Relatorio", tipo_pessoa="PF", cpf_cnpj="REL001", ativo=True)
    session.add(cliente)
    session.flush()
    session.add(Venda(cliente_id=cliente.id, numero="RV001", status="FINALIZADA", valor_total=120))
    session.flush()

    arquivo = _service(session, tmp_path).gerar("vendas", "pdf")

    assert arquivo.exists()
    assert arquivo.read_bytes().startswith(b"%PDF")


def test_relatorio_financeiro_exporta_xlsx(session, tmp_path):
    service = _service(session, tmp_path)

    arquivo = service.gerar("financeiro", "xlsx")

    assert arquivo.exists()
    with ZipFile(arquivo) as xlsx:
        assert "xl/workbook.xml" in xlsx.namelist()
        assert "xl/worksheets/sheet1.xml" in xlsx.namelist()
