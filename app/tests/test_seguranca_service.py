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


def test_backup_cria_copia_do_banco(session, tmp_path):
    database_file = tmp_path / "erp_autopecas.db"
    database_file.write_text("conteudo banco", encoding="utf-8")
    auditoria = AuditoriaService(AuditoriaRepository(session))
    service = BackupService(auditoria, database_file=database_file, backup_dir=tmp_path / "backups")

    backup = service.criar_backup(usuario_id=1)

    assert backup.exists()
    assert backup.read_text(encoding="utf-8") == "conteudo banco"
    assert auditoria.listar()[0].acao == "CRIAR"


def test_restore_substitui_banco_por_backup(session, tmp_path):
    database_file = tmp_path / "erp_autopecas.db"
    database_file.write_text("antigo", encoding="utf-8")
    backup_file = tmp_path / "backup.db"
    backup_file.write_text("restaurado", encoding="utf-8")
    auditoria = AuditoriaService(AuditoriaRepository(session))
    service = BackupService(auditoria, database_file=database_file, backup_dir=tmp_path / "backups")

    service.restaurar_backup(backup_file, usuario_id=1)

    assert database_file.read_text(encoding="utf-8") == "restaurado"
    assert auditoria.listar()[0].acao == "RESTAURAR"
