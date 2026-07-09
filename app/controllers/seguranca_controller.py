from app.database.database import SessionLocal
from app.repositories.seguranca_repository import AuditoriaRepository, ConfiguracaoRepository
from app.services.seguranca_service import AuditoriaService, BackupService, ConfiguracaoService


class SegurancaController:
    def listar_auditoria(self):
        with SessionLocal() as session:
            return AuditoriaService(AuditoriaRepository(session)).listar()

    def listar_configuracoes(self):
        with SessionLocal() as session:
            return ConfiguracaoService(ConfiguracaoRepository(session)).listar()

    def salvar_configuracao(self, chave: str, valor: str | None, usuario_id: int | None = None):
        with SessionLocal() as session:
            auditoria = AuditoriaService(AuditoriaRepository(session))
            configuracao = ConfiguracaoService(ConfiguracaoRepository(session)).salvar(chave, valor)
            auditoria.registrar("configuracao", "SALVAR", chave, usuario_id=usuario_id, entidade_id=configuracao.id)
            session.commit()
            return configuracao

    def criar_backup(self, usuario_id: int | None = None):
        with SessionLocal() as session:
            auditoria = AuditoriaService(AuditoriaRepository(session))
            arquivo = BackupService(auditoria).criar_backup(usuario_id)
            session.commit()
            return arquivo

    def listar_backups(self):
        with SessionLocal() as session:
            auditoria = AuditoriaService(AuditoriaRepository(session))
            return BackupService(auditoria).listar_backups()

    def restaurar_backup(self, arquivo: str, usuario_id: int | None = None):
        with SessionLocal() as session:
            auditoria = AuditoriaService(AuditoriaRepository(session))
            destino = BackupService(auditoria).restaurar_backup(arquivo, usuario_id)
            session.commit()
            return destino
