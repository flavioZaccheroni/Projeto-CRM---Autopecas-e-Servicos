from app.controllers._base import auditar, usuario_atual
from app.database.database import SessionLocal
from app.repositories.seguranca_repository import AuditoriaRepository, ConfiguracaoRepository
from app.services.seguranca_service import AuditoriaService, BackupService, ConfiguracaoService, ler_parametros_backup
from app.utils.logo import caminho_logo, remover_logo, salvar_logo
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

    @requer_permissao("configuracoes", "ver")
    def logo_empresa(self):
        """Caminho do logo da empresa, ou None."""
        return caminho_logo()

    @requer_permissao("configuracoes", "editar")
    def definir_logo(self, origem: str):
        with SessionLocal() as session:
            destino = salvar_logo(origem)
            auditar(session, "configuracao", "LOGO", "logo da empresa atualizado")
            session.commit()
            return destino

    @requer_permissao("configuracoes", "editar")
    def remover_logo(self) -> bool:
        with SessionLocal() as session:
            removido = remover_logo()
            if removido:
                auditar(session, "configuracao", "LOGO", "logo da empresa removido")
                session.commit()
            return removido

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

    # -- rotinas do sistema (sem login/permissao: rodam ao abrir e ao fechar o programa) -------------
    def executar_backup_automatico(self, motivo: str = "abrir") -> dict:
        """Cria o backup automatico quando necessario. Devolve {"criado": bool, "arquivo": Path|None, "aviso": str|None}."""
        with SessionLocal() as session:
            configuracoes = ConfiguracaoService(ConfiguracaoRepository(session))
            parametros = ler_parametros_backup(configuracoes)
            if not parametros["auto"]:
                return {"criado": False, "arquivo": None, "aviso": None}
            servico = BackupService(AuditoriaService(AuditoriaRepository(session)))
            if not servico.precisa_backup_automatico(motivo):
                return {"criado": False, "arquivo": None, "aviso": None}
            arquivo, aviso = servico.backup_automatico(parametros["manter"], parametros["pasta_extra"], usuario_id=None)
            session.commit()
            return {"criado": True, "arquivo": arquivo, "aviso": aviso}

    def situacao_backup(self) -> dict:
        """Resumo para alertas: dias sem backup, limite de alerta e se o automatico esta ligado."""
        with SessionLocal() as session:
            parametros = ler_parametros_backup(ConfiguracaoService(ConfiguracaoRepository(session)))
            servico = BackupService(AuditoriaService(AuditoriaRepository(session)))
            return {
                "dias": servico.dias_sem_backup(),
                "alerta_dias": parametros["alerta_dias"],
                "auto": parametros["auto"],
                "ultimo": servico.ultimo_backup(),
            }
