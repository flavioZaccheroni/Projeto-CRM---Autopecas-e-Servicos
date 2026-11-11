import logging
import sqlite3
from datetime import datetime
from pathlib import Path

from app.config.settings import BACKUPS_DIR, DATABASE_FILE
from app.database.database import engine
from app.models.auditoria import Auditoria
from app.models.configuracao import Configuracao
from app.repositories.seguranca_repository import AuditoriaRepository, ConfiguracaoRepository
from app.utils.validators import validar_obrigatorio

logger = logging.getLogger(__name__)


class AuditoriaService:
    def __init__(self, repository: AuditoriaRepository) -> None:
        self.repository = repository

    def listar(self) -> list[Auditoria]:
        return self.repository.listar()

    def registrar(
        self,
        entidade: str,
        acao: str,
        detalhes: str | None = None,
        usuario_id: int | None = None,
        entidade_id: int | None = None,
    ) -> Auditoria:
        validar_obrigatorio(entidade, "Entidade")
        validar_obrigatorio(acao, "Acao")
        auditoria = Auditoria(
            usuario_id=usuario_id,
            entidade=entidade,
            entidade_id=entidade_id,
            acao=acao,
            detalhes=detalhes,
        )
        logger.info("Auditoria %s %s %s", entidade, acao, detalhes or "")
        return self.repository.salvar(auditoria)


class ConfiguracaoService:
    def __init__(self, repository: ConfiguracaoRepository) -> None:
        self.repository = repository

    def listar(self) -> list[Configuracao]:
        return self.repository.listar()

    def salvar(self, chave: str, valor: str | None) -> Configuracao:
        validar_obrigatorio(chave, "Chave")
        configuracao = self.repository.buscar_por_chave(chave.strip())
        if configuracao is None:
            configuracao = Configuracao(chave=chave.strip())
        configuracao.valor = valor
        return self.repository.salvar(configuracao)


TABELAS_OBRIGATORIAS = {"usuarios", "perfis", "permissoes", "clientes", "produtos", "vendas"}


class BackupService:
    def __init__(
        self,
        auditoria_service: AuditoriaService,
        database_file: Path = DATABASE_FILE,
        backup_dir: Path = BACKUPS_DIR,
    ) -> None:
        self.auditoria_service = auditoria_service
        self.database_file = database_file
        self.backup_dir = backup_dir

    def criar_backup(self, usuario_id: int | None = None) -> Path:
        if not self.database_file.exists():
            raise FileNotFoundError("Banco de dados nao encontrado para backup.")
        destino = self._copiar_banco("erp_autopecas")
        self.auditoria_service.registrar(
            entidade="backup",
            acao="CRIAR",
            detalhes=str(destino),
            usuario_id=usuario_id,
        )
        logger.info("Backup criado em %s", destino)
        return destino

    def listar_backups(self) -> list[Path]:
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        return sorted(self.backup_dir.glob("*.db"), reverse=True)

    def validar_backup(self, arquivo: str | Path, tabelas_obrigatorias: set[str] | None = None) -> Path:
        """Garante que o arquivo e um banco SQLite integro com as tabelas do sistema."""
        origem = Path(arquivo)
        if not origem.is_file() or origem.suffix.lower() != ".db":
            raise ValueError("Arquivo de backup invalido.")
        obrigatorias = TABELAS_OBRIGATORIAS if tabelas_obrigatorias is None else tabelas_obrigatorias
        try:
            conexao = sqlite3.connect(f"file:{origem.as_posix()}?mode=ro", uri=True)
            try:
                resultado = conexao.execute("PRAGMA integrity_check").fetchone()
                tabelas = {linha[0] for linha in conexao.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            finally:
                conexao.close()
        except sqlite3.DatabaseError:
            raise ValueError("O arquivo nao e um banco de dados SQLite valido.") from None
        if not resultado or resultado[0] != "ok":
            raise ValueError("O backup esta corrompido (falha na verificacao de integridade).")
        faltando = obrigatorias - tabelas
        if faltando:
            raise ValueError(f"O arquivo nao parece um backup do sistema (faltam tabelas: {', '.join(sorted(faltando))}).")
        return origem

    def restaurar_backup(self, arquivo: str | Path, usuario_id: int | None = None) -> Path:
        origem = self.validar_backup(arquivo)
        # Rede de seguranca: guarda o estado atual antes de sobrescrever.
        if self.database_file.exists():
            self._copiar_banco("pre_restore")
        self.database_file.parent.mkdir(parents=True, exist_ok=True)
        engine.dispose()
        self._backup_sqlite(origem, self.database_file)
        self.auditoria_service.registrar(
            entidade="backup",
            acao="RESTAURAR",
            detalhes=str(origem),
            usuario_id=usuario_id,
        )
        logger.warning("Backup restaurado de %s", origem)
        return self.database_file

    # -- internos ---------------------------------------------------------------------------
    def _copiar_banco(self, prefixo: str) -> Path:
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        destino = self.backup_dir / f"{prefixo}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.db"
        engine.dispose()
        self._backup_sqlite(self.database_file, destino)
        return destino

    @staticmethod
    def _backup_sqlite(origem: Path, destino: Path) -> None:
        """Copia consistente via API de backup do SQLite (segura mesmo com o banco em uso)."""
        conexao_origem = sqlite3.connect(str(origem))
        conexao_destino = sqlite3.connect(str(destino))
        try:
            conexao_origem.backup(conexao_destino)
        finally:
            conexao_destino.close()
            conexao_origem.close()
