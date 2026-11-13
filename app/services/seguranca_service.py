import logging
import shutil
import sqlite3
from datetime import datetime, timedelta
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

    def obter(self, chave: str, padrao: str | None = None) -> str | None:
        """Valor de um parametro (ou `padrao` se ausente/vazio)."""
        configuracao = self.repository.buscar_por_chave(chave)
        if configuracao is None or configuracao.valor is None or not configuracao.valor.strip():
            return padrao
        return configuracao.valor.strip()

    def salvar(self, chave: str, valor: str | None) -> Configuracao:
        validar_obrigatorio(chave, "Chave")
        configuracao = self.repository.buscar_por_chave(chave.strip())
        if configuracao is None:
            configuracao = Configuracao(chave=chave.strip())
        configuracao.valor = valor
        return self.repository.salvar(configuracao)


TABELAS_OBRIGATORIAS = {"usuarios", "perfis", "permissoes", "clientes", "produtos", "vendas"}

# Backup automatico: parametros (tabela configuracoes) e padroes.
CHAVE_AUTO = "backup.auto"  # "sim" (padrao) ou "nao"
CHAVE_PASTA_EXTRA = "backup.pasta_extra"  # copia adicional (outro disco, pen drive, pasta da nuvem)
CHAVE_MANTER = "backup.manter"  # quantos backups automaticos guardar
CHAVE_ALERTA_DIAS = "backup.alerta_dias"  # avisar se passar tanto tempo sem backup
PADRAO_MANTER = 15
PADRAO_ALERTA_DIAS = 7
PREFIXO_AUTO = "auto"
INTERVALO_ABRIR = timedelta(hours=24)
INTERVALO_SAIR = timedelta(hours=1)


def _inteiro(valor: str | None, padrao: int, minimo: int, maximo: int) -> int:
    try:
        numero = int(str(valor).strip())
    except (TypeError, ValueError):
        return padrao
    return max(minimo, min(maximo, numero))


def ler_parametros_backup(configuracoes: ConfiguracaoService) -> dict:
    """Parametros do backup automatico, com padroes seguros (ligado, 15 copias, alerta em 7 dias)."""
    auto = (configuracoes.obter(CHAVE_AUTO, "sim") or "sim").strip().lower()
    return {
        "auto": auto not in ("nao", "não", "n", "0", "false", "desligado"),
        "pasta_extra": configuracoes.obter(CHAVE_PASTA_EXTRA),
        "manter": _inteiro(configuracoes.obter(CHAVE_MANTER), PADRAO_MANTER, 3, 200),
        "alerta_dias": _inteiro(configuracoes.obter(CHAVE_ALERTA_DIAS), PADRAO_ALERTA_DIAS, 1, 365),
    }


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

    # -- backup automatico ------------------------------------------------------------------
    def ultimo_backup(self) -> datetime | None:
        """Data do backup mais recente (manual ou automatico), ou None se nao houver nenhum."""
        if not self.backup_dir.exists():
            return None
        datas = []
        for arquivo in self.backup_dir.glob("*.db"):
            if arquivo.name.startswith("pre_restore"):
                continue
            try:
                datas.append(datetime.fromtimestamp(arquivo.stat().st_mtime))
            except OSError:
                continue
        return max(datas) if datas else None

    def dias_sem_backup(self, agora: datetime | None = None) -> int | None:
        """Dias desde o ultimo backup; None se nunca houve."""
        ultimo = self.ultimo_backup()
        if ultimo is None:
            return None
        return max(0, ((agora or datetime.now()) - ultimo).days)

    def precisa_backup_automatico(self, motivo: str, agora: datetime | None = None) -> bool:
        """Decide se vale criar um backup agora.

        - "abrir": se nunca houve backup, ou se o banco mudou e o ultimo tem 24 h ou mais;
        - "sair": se o banco mudou depois do ultimo backup (no maximo um por hora).
        Sem alteracoes desde o ultimo backup, nao cria copia repetida.
        """
        if not self.database_file.exists():
            return False
        agora = agora or datetime.now()
        ultimo = self.ultimo_backup()
        if ultimo is None:
            return True
        banco_alterado = datetime.fromtimestamp(self.database_file.stat().st_mtime) > ultimo
        if not banco_alterado:
            return False
        intervalo = INTERVALO_SAIR if motivo == "sair" else INTERVALO_ABRIR
        return (agora - ultimo) >= intervalo

    def backup_automatico(
        self,
        manter: int = PADRAO_MANTER,
        pasta_extra: str | Path | None = None,
        usuario_id: int | None = None,
    ) -> tuple[Path, str | None]:
        """Cria um backup `auto_*`, copia para a pasta extra (se houver) e limpa os mais antigos.

        Devolve (arquivo, aviso). O aviso descreve uma falha ao copiar para a pasta extra: o backup local
        ja foi feito, entao essa falha nunca derruba a rotina.
        """
        if not self.database_file.exists():
            raise FileNotFoundError("Banco de dados nao encontrado para backup.")
        destino = self._copiar_banco(PREFIXO_AUTO)
        aviso = None
        if pasta_extra and str(pasta_extra).strip():
            aviso = self._copiar_para_pasta_extra(destino, Path(str(pasta_extra).strip()), manter)
        self._aplicar_retencao(self.backup_dir, manter)
        self.auditoria_service.registrar(
            entidade="backup",
            acao="CRIAR_AUTO",
            detalhes=str(destino) + (f" | pasta extra: {aviso}" if aviso else ""),
            usuario_id=usuario_id,
        )
        logger.info("Backup automatico criado em %s", destino)
        return destino, aviso

    def _copiar_para_pasta_extra(self, arquivo: Path, pasta: Path, manter: int) -> str | None:
        try:
            pasta.mkdir(parents=True, exist_ok=True)
            shutil.copy2(arquivo, pasta / arquivo.name)
            self._aplicar_retencao(pasta, manter)
        except OSError as exc:
            logger.warning("Nao foi possivel copiar o backup para %s: %s", pasta, exc)
            return f"Nao foi possivel copiar para {pasta} ({exc.strerror or exc})."
        return None

    @staticmethod
    def _aplicar_retencao(pasta: Path, manter: int) -> None:
        """Apaga os backups `auto_*` mais antigos, mantendo os `manter` mais recentes. Backups manuais nunca sao apagados."""
        automaticos = sorted(pasta.glob(f"{PREFIXO_AUTO}_*.db"), key=lambda a: a.name, reverse=True)
        for antigo in automaticos[manter:]:
            try:
                antigo.unlink()
            except OSError as exc:
                logger.warning("Nao foi possivel apagar o backup antigo %s: %s", antigo, exc)

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
