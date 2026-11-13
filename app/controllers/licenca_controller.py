"""Licenca e periodo de teste: estado atual, ativacao de arquivo de licenca e modo somente consulta.

`situacao()` e `aplicar_restricao()` rodam sem login (a tela de login ja mostra o estado). `ativar()` exige usuario logado.
O inicio do teste fica gravado em dois lugares (tabela de configuracoes e um marcador na pasta do programa/dados);
vale o mais antigo, e a data nunca volta atras (relogio adiantado/atrasado nao reinicia o teste).
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import date
from pathlib import Path

from app.config.settings import DATA_DIR, ROOT_DIR
from app.controllers._base import auditar
from app.database.database import SessionLocal
from app.repositories.seguranca_repository import ConfiguracaoRepository
from app.services import licenca_service
from app.services.licenca_service import LicencaInvalida, Situacao
from app.services.seguranca_service import ConfiguracaoService
from app.utils.maquina import codigo_da_maquina
from app.utils.sessao import Sessao

logger = logging.getLogger(__name__)

CHAVE_PRIMEIRO_USO = "licenca.primeiro_uso"
CHAVE_ULTIMO_USO = "licenca.ultimo_uso"
ARQUIVO_LICENCA = DATA_DIR / f"licenca{licenca_service.EXTENSAO}"
MARCADOR = ROOT_DIR / ".erp_inicio"


def _data(texto: str | None) -> date | None:
    try:
        return date.fromisoformat((texto or "").strip())
    except ValueError:
        return None


def _ler_marcador(marcador: Path) -> tuple[date | None, date | None]:
    try:
        linhas = marcador.read_text(encoding="utf-8").split()
    except OSError:
        return None, None
    return (_data(linhas[0]) if linhas else None), (_data(linhas[1]) if len(linhas) > 1 else None)


def _gravar_marcador(marcador: Path, primeiro: date, ultimo: date) -> None:
    try:
        marcador.parent.mkdir(parents=True, exist_ok=True)
        marcador.write_text(f"{primeiro.isoformat()}\n{ultimo.isoformat()}\n", encoding="utf-8")
    except OSError:
        logger.warning("Nao foi possivel gravar o marcador de teste em %s", marcador)


def _livre_para_desenvolvimento() -> bool:
    return not getattr(sys, "frozen", False) and os.environ.get("ERP_LICENCA_LIVRE") == "1"


class LicencaController:
    def __init__(self, arquivo_licenca: Path | None = None, marcador: Path | None = None) -> None:
        self.arquivo_licenca = arquivo_licenca or ARQUIVO_LICENCA
        self.marcador = marcador or MARCADOR

    def _datas_de_uso(self, hoje_real: date) -> tuple[date, date]:
        """(primeiro uso, hoje efetivo), registrando os dois nos dois lugares."""
        primeiro_db = ultimo_db = None
        try:
            with SessionLocal() as session:
                config = ConfiguracaoService(ConfiguracaoRepository(session))
                primeiro_db, ultimo_db = _data(config.obter(CHAVE_PRIMEIRO_USO)), _data(config.obter(CHAVE_ULTIMO_USO))
                primeiro_marc, ultimo_marc = _ler_marcador(self.marcador)
                candidatos_ultimo = [d for d in (ultimo_db, ultimo_marc, hoje_real) if d]
                hoje = max(candidatos_ultimo)
                primeiro = min([d for d in (primeiro_db, primeiro_marc) if d] or [hoje])
                if primeiro_db != primeiro:
                    config.salvar(CHAVE_PRIMEIRO_USO, primeiro.isoformat())
                if ultimo_db != hoje:
                    config.salvar(CHAVE_ULTIMO_USO, hoje.isoformat())
                session.commit()
        except Exception:  # noqa: BLE001 - sem banco, usa so o marcador; a licenca nunca derruba o sistema
            logger.exception("Nao foi possivel ler/gravar as datas de uso no banco")
            primeiro_marc, ultimo_marc = _ler_marcador(self.marcador)
            hoje = max([d for d in (ultimo_marc, hoje_real) if d])
            primeiro = min([d for d in (primeiro_db, primeiro_marc) if d] or [hoje])
        _gravar_marcador(self.marcador, primeiro, hoje)
        return primeiro, hoje

    def situacao(self, hoje: date | None = None) -> Situacao:
        primeiro, hoje_efetivo = self._datas_de_uso(hoje or date.today())
        dados, erro = None, None
        if self.arquivo_licenca.is_file():
            try:
                dados = licenca_service.ler_arquivo(self.arquivo_licenca)
            except LicencaInvalida as exc:
                erro = str(exc)
        return licenca_service.avaliar(hoje_efetivo, dados, primeiro, codigo_da_maquina(), erro)

    def codigo_maquina(self) -> str:
        return codigo_da_maquina()

    def aplicar_restricao(self) -> Situacao:
        """Liga/desliga o modo somente consulta da sessao conforme a situacao atual."""
        situacao = self.situacao()
        Sessao.somente_consulta = situacao.somente_consulta and not _livre_para_desenvolvimento()
        return situacao

    def ativar(self, caminho: str) -> Situacao:
        """Valida o arquivo escolhido, guarda-o na pasta de dados e libera o sistema. Levanta LicencaInvalida se recusado."""
        Sessao.exigir_autenticado()
        dados = licenca_service.ler_arquivo(Path(caminho))
        alvo = dados.get("maquina")
        if alvo and licenca_service.normalizar_maquina(alvo) != licenca_service.normalizar_maquina(codigo_da_maquina()):
            raise LicencaInvalida("Esta licença foi emitida para outro computador.")
        if dados.get("validade") and date.fromisoformat(dados["validade"]) < date.today():
            raise LicencaInvalida(f"Esta licença já venceu em {date.fromisoformat(dados['validade']):%d/%m/%Y}.")
        self.arquivo_licenca.parent.mkdir(parents=True, exist_ok=True)
        self.arquivo_licenca.write_text(Path(caminho).read_text(encoding="utf-8"), encoding="utf-8")
        with SessionLocal() as session:
            auditar(session, "licenca", "ATIVAR", f"{dados['cliente']} | {dados['plano']} | validade {dados.get('validade') or 'sem vencimento'}")
            session.commit()
        return self.aplicar_restricao()
