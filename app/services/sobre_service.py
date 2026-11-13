"""Informacoes do sistema para a tela Sobre e para o suporte (somente leitura, sem dados de clientes)."""

from __future__ import annotations

import platform
import sqlite3
import sys
from pathlib import Path

from app.config import settings


def modo_de_execucao() -> str:
    if not getattr(sys, "frozen", False):
        return "Código-fonte (Python)"
    portatil = settings.ROOT_DIR == Path(sys.executable).resolve().parent
    return "Executável (portátil, dados ao lado do programa)" if portatil else "Executável (dados na pasta do usuário)"


def _tamanho_legivel(tamanho: int) -> str:
    if tamanho >= 1024 * 1024:
        return f"{tamanho / 1024 / 1024:.1f} MB"
    return f"{tamanho / 1024:.0f} KB"


def _versoes_qt() -> tuple[str, str]:
    try:
        import PySide6
        from PySide6.QtCore import qVersion

        return PySide6.__version__, qVersion()
    except Exception:  # noqa: BLE001 - informacao opcional
        return "?", "?"


def _versao_do_banco() -> str:
    try:
        from app.database.alembic_runner import versao_atual
        from app.database.database import engine

        return versao_atual(engine) or "?"
    except Exception:  # noqa: BLE001 - nunca impede abrir a tela
        return "?"


def coletar_informacoes(situacao_backup: dict | None = None) -> dict:
    """Reune versao, ambiente, pastas e estado do banco/backup. `situacao_backup` vem do controller de seguranca."""
    pyside, qt = _versoes_qt()
    banco = settings.DATABASE_FILE
    try:
        tamanho_banco = _tamanho_legivel(banco.stat().st_size)
    except OSError:
        tamanho_banco = "banco ainda não criado"
    ultimo = (situacao_backup or {}).get("ultimo")
    backup = "nenhum backup ainda" if ultimo is None else f"{ultimo:%d/%m/%Y %H:%M}"
    auto = (situacao_backup or {}).get("auto")
    return {
        "nome": settings.APP_NAME,
        "versao": settings.APP_VERSION,
        "aviso": settings.AVISO_DEMO,
        "modo": modo_de_execucao(),
        "sistema": platform.platform(),
        "python": platform.python_version(),
        "pyside": pyside,
        "qt": qt,
        "sqlite": sqlite3.sqlite_version,
        "pasta_dados": settings.DATA_DIR,
        "banco": banco,
        "tamanho_banco": tamanho_banco,
        "versao_banco": _versao_do_banco(),
        "pasta_logs": settings.LOGS_DIR,
        "pasta_backups": settings.BACKUPS_DIR,
        "ultimo_backup": backup,
        "backup_automatico": "não informado" if auto is None else ("ligado" if auto else "desligado"),
    }


def texto_para_suporte(info: dict) -> str:
    """Bloco de texto para colar em e-mail/WhatsApp. Nao inclui senhas, dados de clientes nem conteudo dos logs."""
    linhas = [
        f"{info['nome']} — versão {info['versao']}",
        f"Modo: {info['modo']}",
        f"Sistema operacional: {info['sistema']}",
        f"Python {info['python']} · PySide6 {info['pyside']} (Qt {info['qt']}) · SQLite {info['sqlite']}",
        f"Banco: {info['banco']} ({info['tamanho_banco']}, schema {info['versao_banco']})",
        f"Logs: {info['pasta_logs']}",
        f"Backups: {info['pasta_backups']}",
        f"Último backup: {info['ultimo_backup']} · automático {info['backup_automatico']}",
    ]
    return "\n".join(linhas)
