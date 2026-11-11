from sqlalchemy import create_engine, inspect, text

from app.database.migrations import aplicar_migracoes


def _colunas(engine, tabela):
    return {coluna["name"] for coluna in inspect(engine).get_columns(tabela)}


def test_migracao_adiciona_colunas_sem_perder_dados(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'antigo.db'}")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE usuarios (id INTEGER PRIMARY KEY, nome TEXT, login TEXT)"))
        conn.execute(text("INSERT INTO usuarios (nome, login) VALUES ('Admin', 'admin')"))
        conn.execute(text("CREATE TABLE vendas (id INTEGER PRIMARY KEY, numero TEXT)"))
        conn.execute(text("INSERT INTO vendas (numero) VALUES ('V001')"))

    criadas = aplicar_migracoes(engine)

    assert "usuarios.precisa_trocar_senha" in criadas
    assert {"precisa_trocar_senha", "tentativas_falhas", "bloqueado_ate"} <= _colunas(engine, "usuarios")
    assert {"forma_pagamento", "parcelas", "motivo_cancelamento"} <= _colunas(engine, "vendas")
    with engine.connect() as conn:
        assert conn.execute(text("SELECT login, tentativas_falhas FROM usuarios")).fetchone() == ("admin", 0)
        assert conn.execute(text("SELECT numero, parcelas FROM vendas")).fetchone() == ("V001", 1)


def test_migracao_e_idempotente(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'antigo.db'}")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE compras (id INTEGER PRIMARY KEY)"))

    assert aplicar_migracoes(engine) == ["compras.motivo_cancelamento"]
    assert aplicar_migracoes(engine) == []
