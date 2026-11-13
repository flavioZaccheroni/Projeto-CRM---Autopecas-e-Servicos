from sqlalchemy import create_engine, inspect, text

from app.database.alembic_runner import upgrade_to_head, versao_atual
from app.database.database import importar_modelos


def test_banco_novo_chega_ao_head_com_todas_as_tabelas(tmp_path):
    importar_modelos()
    engine = create_engine(f"sqlite:///{tmp_path / 'novo.db'}")
    upgrade_to_head(engine)
    tabelas = set(inspect(engine).get_table_names())
    assert {"usuarios", "vendas", "ordens_servico", "compras", "auditoria", "alembic_version"} <= tabelas
    assert versao_atual(engine) == "0003"


def test_banco_anterior_ao_alembic_e_atualizado_sem_perder_dados(tmp_path):
    importar_modelos()
    engine = create_engine(f"sqlite:///{tmp_path / 'antigo.db'}")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE usuarios (id INTEGER PRIMARY KEY, nome TEXT, login TEXT)"))
        conn.execute(text("INSERT INTO usuarios (nome, login) VALUES ('Admin', 'admin')"))
    upgrade_to_head(engine)
    colunas = {c["name"] for c in inspect(engine).get_columns("usuarios")}
    assert {"precisa_trocar_senha", "tentativas_falhas", "bloqueado_ate"} <= colunas
    with engine.connect() as conn:
        assert conn.execute(text("SELECT login FROM usuarios")).scalar() == "admin"


def test_upgrade_e_idempotente(tmp_path):
    importar_modelos()
    engine = create_engine(f"sqlite:///{tmp_path / 'x.db'}")
    upgrade_to_head(engine)
    upgrade_to_head(engine)
    assert versao_atual(engine) == "0003"


def test_base_em_0001_ganha_desconto_e_acrescimo_sem_perder_vendas(tmp_path):
    importar_modelos()
    engine = create_engine(f"sqlite:///{tmp_path / 'v1.db'}")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE vendas (id INTEGER PRIMARY KEY, valor_total NUMERIC(12,2) NOT NULL DEFAULT 0)"))
        conn.execute(text("INSERT INTO vendas (valor_total) VALUES (42)"))
    upgrade_to_head(engine)
    colunas = {c["name"] for c in inspect(engine).get_columns("vendas")}
    assert {"desconto", "acrescimo"} <= colunas
    with engine.connect() as conn:
        assert conn.execute(text("SELECT valor_total, desconto, acrescimo FROM vendas")).one() == (42, 0, 0)


def test_base_em_0002_ganha_servicos_e_mecanico(tmp_path):
    importar_modelos()
    engine = create_engine(f"sqlite:///{tmp_path / 'v2.db'}")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE ordens_servico (id INTEGER PRIMARY KEY, numero TEXT)"))
        conn.execute(text("INSERT INTO ordens_servico (numero) VALUES ('OS000001')"))
    upgrade_to_head(engine)
    assert "servicos" in set(inspect(engine).get_table_names())
    assert "mecanico" in {c["name"] for c in inspect(engine).get_columns("ordens_servico")}
    with engine.connect() as conn:
        assert conn.execute(text("SELECT numero FROM ordens_servico")).scalar() == "OS000001"
