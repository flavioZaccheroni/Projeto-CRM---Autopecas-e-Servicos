import pytest

from app.utils.parcelas import gerar_parcelas
from app.utils.validators import (
    cnpj_valido,
    cpf_valido,
    placa_valida,
    validar_cpf_cnpj,
    validar_senha_forte,
    validar_telefone_opcional,
    validar_uf_opcional,
)
from datetime import date
from decimal import Decimal


def test_cpf_valido_e_invalido():
    assert cpf_valido("529.982.247-25")
    assert cpf_valido("52998224725")
    assert not cpf_valido("529.982.247-24")  # digito verificador errado
    assert not cpf_valido("111.111.111-11")  # sequencia repetida
    assert not cpf_valido("123")


def test_cnpj_valido_e_invalido():
    assert cnpj_valido("11.222.333/0001-81")
    assert not cnpj_valido("11.222.333/0001-80")
    assert not cnpj_valido("00.000.000/0000-00")


def test_validar_cpf_cnpj_respeita_tipo_pessoa():
    validar_cpf_cnpj("529.982.247-25", "PF")
    validar_cpf_cnpj("11.222.333/0001-81", "PJ")
    with pytest.raises(ValueError, match="CPF invalido"):
        validar_cpf_cnpj("11.222.333/0001-81", "PF")
    with pytest.raises(ValueError, match="CNPJ invalido"):
        validar_cpf_cnpj("529.982.247-25", "PJ")


def test_placa_antiga_e_mercosul():
    assert placa_valida("ABC1234")
    assert placa_valida("abc-1234")
    assert placa_valida("ABC1D23")
    assert not placa_valida("AB12345")
    assert not placa_valida("")


def test_uf_e_telefone():
    validar_uf_opcional("SP")
    validar_uf_opcional("")
    with pytest.raises(ValueError):
        validar_uf_opcional("XX")
    validar_telefone_opcional("(11) 98765-4321")
    with pytest.raises(ValueError):
        validar_telefone_opcional("12345")


@pytest.mark.parametrize("senha", ["curta1", "somenteletras", "12345678"])
def test_senha_fraca_e_rejeitada(senha):
    with pytest.raises(ValueError):
        validar_senha_forte(senha)


def test_senha_forte_aceita():
    validar_senha_forte("Senha1234")


def test_parcelas_somam_o_total_e_resto_vai_na_ultima():
    parcelas = gerar_parcelas(Decimal("100.00"), 3, date(2026, 1, 10))

    assert [valor for valor, _ in parcelas] == [Decimal("33.33"), Decimal("33.33"), Decimal("33.34")]
    assert sum(valor for valor, _ in parcelas) == Decimal("100.00")
    assert [data for _, data in parcelas] == [date(2026, 1, 10), date(2026, 2, 9), date(2026, 3, 11)]


def test_parcelas_quantidade_invalida():
    with pytest.raises(ValueError):
        gerar_parcelas(Decimal("10"), 0, date(2026, 1, 1))
