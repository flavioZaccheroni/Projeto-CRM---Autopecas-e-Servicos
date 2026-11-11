import sqlite3

import pytest

from app.repositories.seguranca_repository import AuditoriaRepository, ConfiguracaoRepository
from app.services.seguranca_service import AuditoriaService, BackupService, ConfiguracaoService


def test_configuracao_salva_e_atualiza_por_chave(session):
    service = ConfiguracaoService(ConfiguracaoRepository(session))

    service.salvar("empresa.nome", "Autopecas Teste")
    service.salvar("empresa.nome", "Autopecas Atualizada")

    configuracoes = service.listar()
    assert len(configuracoes) == 1
    assert configuracoes[0].valor == "Autopecas Atualizada"


def test_auditoria_registra_evento(session):
    service = AuditoriaService(AuditoriaRepository(session))

    evento = service.registrar("backup", "CRIAR", "arquivo.db", usuario_id=1)

    assert evento.entidade == "backup"
    assert evento.acao == "CRIAR"
    assert service.listar()[0].detalhes == "arquivo.db"


def _criar_banco(caminho, valor="x", tabelas=("usuarios", "perfis", "permissoes", "clientes", "produtos", "vendas")):
    conexao = sqlite3.connect(caminho)
    for tabela in tabelas:
        conexao.execute(f"CREATE TABLE {tabela} (id INTEGER PRIMARY KEY, valor TEXT)")
    if tabelas:
        conexao.execute(f"INSERT INTO {tabelas[0]} (valor) VALUES (?)", (valor,))
    conexao.commit()
    conexao.close()


def _valor(caminho):
    conexao = sqlite3.connect(caminho)
    try:
        return conexao.execute("SELECT valor FROM usuarios").fetchone()[0]
    finally:
        conexao.close()


def _service(session, tmp_path):
    auditoria = AuditoriaService(AuditoriaRepository(session))
    return auditoria, BackupService(auditoria, database_file=tmp_path / "erp.db", backup_dir=tmp_path / "backups")


def test_backup_cria_copia_do_banco(session, tmp_path):
    _criar_banco(tmp_path / "erp.db", "dados")
    auditoria, service = _service(session, tmp_path)

    backup = service.criar_backup(usuario_id=1)

    assert backup.exists()
    assert _valor(backup) == "dados"
    assert auditoria.listar()[0].acao == "CRIAR"


def test_restore_substitui_banco_e_guarda_estado_anterior(session, tmp_path):
    _criar_banco(tmp_path / "erp.db", "antigo")
    _criar_banco(tmp_path / "backup.db", "restaurado")
    auditoria, service = _service(session, tmp_path)

    service.restaurar_backup(tmp_path / "backup.db", usuario_id=1)

    assert _valor(tmp_path / "erp.db") == "restaurado"
    assert auditoria.listar()[0].acao == "RESTAURAR"
    pre_restore = [arquivo for arquivo in service.listar_backups() if arquivo.name.startswith("pre_restore_")]
    assert len(pre_restore) == 1
    assert _valor(pre_restore[0]) == "antigo"


def test_restore_rejeita_arquivo_que_nao_e_sqlite(session, tmp_path):
    _criar_banco(tmp_path / "erp.db", "intacto")
    (tmp_path / "lixo.db").write_text("isto nao e um banco", encoding="utf-8")
    _auditoria, service = _service(session, tmp_path)

    with pytest.raises(ValueError, match="SQLite"):
        service.restaurar_backup(tmp_path / "lixo.db")

    assert _valor(tmp_path / "erp.db") == "intacto"


def test_restore_rejeita_banco_sem_tabelas_do_sistema(session, tmp_path):
    _criar_banco(tmp_path / "erp.db", "intacto")
    _criar_banco(tmp_path / "outro.db", tabelas=("qualquer_coisa",))
    _auditoria, service = _service(session, tmp_path)

    with pytest.raises(ValueError, match="faltam tabelas"):
        service.restaurar_backup(tmp_path / "outro.db")

    assert _valor(tmp_path / "erp.db") == "intacto"
