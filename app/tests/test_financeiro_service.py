import pytest

from app.repositories.financeiro_repository import CaixaMovimentacaoRepository, FinanceiroRepository
from app.services.financeiro_service import FinanceiroService


def test_baixar_receber_movimenta_caixa_entrada(session):
    service = FinanceiroService(FinanceiroRepository(session), CaixaMovimentacaoRepository(session))
    lancamento = service.criar_lancamento(
        {
            "tipo": "RECEBER",
            "descricao": "Recebimento teste",
            "valor": "150",
            "data_vencimento": "2026-07-09",
        }
    )

    service.baixar_lancamento(lancamento.id, "PIX")

    caixa = service.listar_caixa()
    resumo = service.resumo_fluxo()
    assert lancamento.status == "PAGO"
    assert caixa[0].tipo == "ENTRADA"
    assert caixa[0].valor == 150
    assert resumo["saldo_caixa"] == 150


def test_baixar_pagar_movimenta_caixa_saida(session):
    service = FinanceiroService(FinanceiroRepository(session), CaixaMovimentacaoRepository(session))
    lancamento = service.criar_lancamento(
        {
            "tipo": "PAGAR",
            "descricao": "Pagamento teste",
            "valor": "40",
            "data_vencimento": "2026-07-09",
        }
    )

    service.baixar_lancamento(lancamento.id, "DINHEIRO")

    assert service.saldo_caixa() == -40


def test_estornar_lancamento_pago_preserva_historico_e_inverte_caixa(session):
    service = FinanceiroService(FinanceiroRepository(session), CaixaMovimentacaoRepository(session))
    lancamento = service.criar_lancamento(
        {
            "tipo": "RECEBER",
            "descricao": "Recebimento estorno",
            "valor": "75",
            "data_vencimento": "2026-07-09",
        }
    )
    service.baixar_lancamento(lancamento.id, "PIX")

    service.estornar_lancamento(lancamento.id)

    caixa = service.listar_caixa()
    assert lancamento.status == "ESTORNADO"
    assert len(caixa) == 2
    assert caixa[1].tipo == "SAIDA"
    assert service.saldo_caixa() == 0


def test_nao_baixa_lancamento_pago_duas_vezes(session):
    service = FinanceiroService(FinanceiroRepository(session), CaixaMovimentacaoRepository(session))
    lancamento = service.criar_lancamento(
        {
            "tipo": "RECEBER",
            "descricao": "Duplicidade",
            "valor": "20",
            "data_vencimento": "2026-07-09",
        }
    )
    service.baixar_lancamento(lancamento.id, "PIX")

    with pytest.raises(ValueError, match="ja esta pago"):
        service.baixar_lancamento(lancamento.id, "PIX")
