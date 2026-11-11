from app.controllers._base import auditar, usuario_atual
from app.database.database import SessionLocal
from app.repositories.seguranca_repository import AuditoriaRepository, ConfiguracaoRepository
from app.services.seguranca_service import AuditoriaService, BackupService, ConfiguracaoService
from app.utils.sessao import requer_permissao


class SegurancaController:
    @requer_permissao("seguranca", "ver")
    def listar_auditoria(self):
        with SessionLocal() as session:
            return AuditoriaService(AuditoriaRepository(session)).listar()

    @requer_permissao("configuracoes", "ver")
    def listar_configuracoes(self):
        with SessionLocal() as session:
            return ConfiguracaoService(ConfiguracaoRepository(session)).listar()

    @requer_permissao("configuracoes", "editar")
    def salvar_configuracao(self, chave: str, valor: str | None, usuario_id: int | None = None):
        with SessionLocal() as session:
            configuracao = ConfiguracaoService(ConfiguracaoRepository(session)).salvar(chave, valor)
            auditar(session, "configuracao", "SALVAR", f"{chave}={valor}", configuracao.id)
            session.commit()
            return configuracao

    @requer_permissao("seguranca", "criar")
    def criar_backup(self, usuario_id: int | None = None):
        with SessionLocal() as session:
            auditoria = AuditoriaService(AuditoriaRepository(session))
            arquivo = BackupService(auditoria).criar_backup(usuario_atual(usuario_id))
            session.commit()
            return arquivo

    @requer_permissao("seguranca", "ver")
    def listar_backups(self):
        with SessionLocal() as session:
            auditoria = AuditoriaService(AuditoriaRepository(session))
            return BackupService(auditoria).listar_backups()

    @requer_permissao("seguranca", "excluir")
    def restaurar_backup(self, arquivo: str, usuario_id: int | None = None):
        with SessionLocal() as session:
            auditoria = AuditoriaService(AuditoriaRepository(session))
            destino = BackupService(auditoria).restaurar_backup(arquivo, usuario_atual(usuario_id))
            session.commit()
            return destino
