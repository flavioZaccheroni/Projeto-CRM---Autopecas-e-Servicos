from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace

from app.utils.busca import extrair_id, filtrar_linhas, normalizar, titulo_coluna, valor_coluna
from app.utils.formatacao import format_value


def test_normalizar_remove_acentos_e_caixa():
    assert normalizar("Peças Ótimas") == "pecas otimas"
    assert normalizar(None) == ""


def test_extrair_id():
    assert extrair_id("12 - Filtro de oleo") == "12"
    assert extrair_id(" 7 ") == "7"
    assert extrair_id("Filtro") == ""
    assert extrair_id("") == ""


def test_filtrar_linhas_todas_as_palavras_sem_acento():
    linhas = [("1", ["Joao", "Peças"]), ("2", ["Maria", "Servico"]), ("3", ["Joao", "Servico"])]
    assert [i for i, _ in filtrar_linhas(linhas, "joao servico")] == ["3"]
    assert [i for i, _ in filtrar_linhas(linhas, "PECAS")] == ["1"]
    assert len(filtrar_linhas(linhas, "  ")) == 3


def test_valor_coluna_aninhado_e_nulo():
    obj = SimpleNamespace(cliente=SimpleNamespace(nome="Ana"), vazio=None)
    assert valor_coluna(obj, "cliente.nome") == "Ana"
    assert valor_coluna(obj, "vazio.nome") == ""


def test_titulo_coluna():
    assert titulo_coluna("id") == "ID"
    assert titulo_coluna("produto.descricao") == "Produto"
    assert titulo_coluna("data_venda") == "Data venda"


def test_format_value():
    assert format_value(True) == "Sim"
    assert format_value(False) == "Nao"
    assert format_value(date(2026, 3, 5)) == "05/03/2026"
    assert format_value(datetime(2026, 3, 5, 14, 30)) == "05/03/2026 14:30"
    assert format_value(Decimal("1234.5")).endswith("1.234,50") or format_value(Decimal("1234.5")) == "1234,50"
    assert format_value(None) == ""
