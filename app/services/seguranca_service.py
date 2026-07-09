import logging
import shutil
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
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        destino = self.backup_dir / f"erp_autopecas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        engine.dispose()
        shutil.copy2(self.database_file, destino)
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

    def restaurar_backup(self, arquivo: str | Path, usuario_id: int | None = None) -> Path:
        origem = Path(arquivo)
        if not origem.exists() or origem.suffix.lower() != ".db":
            raise ValueError("Arquivo de backup invalido.")
        self.database_file.parent.mkdir(parents=True, exist_ok=True)
        engine.dispose()
        shutil.copy2(origem, self.database_file)
        self.auditoria_service.registrar(
            entidade="backup",
            acao="RESTAURAR",
            detalhes=str(origem),
            usuario_id=usuario_id,
        )
        logger.warning("Backup restaurado de %s", origem)
        return self.database_file
