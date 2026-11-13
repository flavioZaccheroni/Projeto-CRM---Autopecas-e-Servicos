"""Licenca offline e periodo de teste do ERP.

- A licenca e um arquivo `.erplic` (JSON) assinado com Ed25519: `{"dados": {...}, "assinatura": "<base64>"}`.
  O app so verifica (chave publica embutida); quem assina e o script do fornecedor (scripts/gerar_licenca.py).
- Sem licenca valida, o sistema funciona por TESTE_DIAS a partir do primeiro uso; depois entra em modo somente
  consulta (ver, exportar, fazer backup): os dados do cliente nunca sao bloqueados nem apagados.
- Limite honesto: em app local, nada impede um invasor determinado. O objetivo e evitar o uso casual sem pagar.
"""

from __future__ import annotations

import base64
import binascii
import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from app.utils import ed25519

TESTE_DIAS = 30
AVISO_VENCIMENTO_DIAS = 15  # avisa a licenca que vence em ate N dias
FORMATO = 1
EXTENSAO = ".erplic"

# Chave publica Ed25519 (hex, 32 bytes) do fornecedor. A chave privada correspondente NAO fica neste repositorio.
CHAVE_PUBLICA_HEX = "769263c980a7d0585e91a485123086c452f35682a0cad0189110d6efe094c44b"

CAMPOS_TEXTO = ("cliente", "documento", "plano")


class LicencaInvalida(ValueError):
    """Arquivo de licenca ilegivel, adulterado ou de outro computador."""


@dataclass
class Situacao:
    estado: str  # licenciado | teste | teste_encerrado | licenca_expirada
    titulo: str  # texto curto (barra lateral)
    detalhe: str  # texto completo (tela Sobre / tooltip)
    dias_restantes: int | None = None  # None = sem prazo (licenca perpetua)
    licenca: dict | None = None
    erro: str | None = None  # problema com o arquivo de licenca presente (se houver)

    @property
    def somente_consulta(self) -> bool:
        return self.estado in ("teste_encerrado", "licenca_expirada")

    @property
    def precisa_aviso(self) -> bool:
        if self.somente_consulta:
            return True
        return self.dias_restantes is not None and self.dias_restantes <= (7 if self.estado == "teste" else AVISO_VENCIMENTO_DIAS)


# -- formato do arquivo ---------------------------------------------------------------------
def _canonico(dados: dict) -> bytes:
    return json.dumps(dados, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def montar_licenca(
    chave_privada: bytes,
    cliente: str,
    plano: str,
    validade: date | None,
    emitida: date,
    documento: str = "",
    maquina: str | None = None,
) -> str:
    """Gera o conteudo do arquivo de licenca (usado pelo script do fornecedor e pelos testes)."""
    if not cliente.strip():
        raise ValueError("Informe o nome do cliente.")
    dados = {
        "v": FORMATO,
        "cliente": cliente.strip(),
        "documento": documento.strip(),
        "plano": plano.strip() or "Padrao",
        "emitida": emitida.isoformat(),
        "validade": validade.isoformat() if validade else None,
        "maquina": normalizar_maquina(maquina) if maquina else None,
    }
    assinatura = ed25519.assinar(chave_privada, _canonico(dados))
    return json.dumps({"dados": dados, "assinatura": base64.b64encode(assinatura).decode("ascii")}, indent=2, ensure_ascii=True)


def normalizar_maquina(codigo: str) -> str:
    return "".join(c for c in str(codigo).upper() if c.isalnum())


def ler_licenca(conteudo: str, chave_publica: bytes | None = None) -> dict:
    """Valida assinatura e estrutura. Devolve os dados da licenca ou levanta LicencaInvalida."""
    chave = chave_publica if chave_publica is not None else bytes.fromhex(CHAVE_PUBLICA_HEX)
    try:
        bruto = json.loads(conteudo)
        dados, assinatura = bruto["dados"], base64.b64decode(bruto["assinatura"], validate=True)
    except (ValueError, KeyError, TypeError, binascii.Error):
        raise LicencaInvalida("O arquivo não é uma licença válida.") from None
    if not isinstance(dados, dict) or not ed25519.verificar(chave, _canonico(dados), assinatura):
        raise LicencaInvalida("A assinatura da licença não confere (arquivo alterado ou de outro emissor).")
    if dados.get("v") != FORMATO or not all(isinstance(dados.get(c), str) for c in CAMPOS_TEXTO):
        raise LicencaInvalida("Formato de licença não suportado por esta versão do sistema.")
    for campo in ("emitida", "validade"):
        valor = dados.get(campo)
        if valor is None and campo == "validade":
            continue
        try:
            date.fromisoformat(str(valor))
        except ValueError:
            raise LicencaInvalida("A licença tem uma data inválida.") from None
    return dados


def ler_arquivo(caminho: Path, chave_publica: bytes | None = None) -> dict:
    try:
        conteudo = Path(caminho).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        raise LicencaInvalida("Não foi possível ler o arquivo de licença.") from None
    return ler_licenca(conteudo, chave_publica)


# -- avaliacao ------------------------------------------------------------------------------
def _fmt(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def avaliar(
    hoje: date,
    licenca: dict | None,
    primeiro_uso: date,
    maquina_atual: str,
    erro: str | None = None,
    teste_dias: int = TESTE_DIAS,
) -> Situacao:
    """Decide o estado a partir da licenca (ja validada), do primeiro uso e do computador atual."""
    if licenca is not None:
        alvo = licenca.get("maquina")
        if alvo and normalizar_maquina(alvo) != normalizar_maquina(maquina_atual):
            erro = "Esta licença foi emitida para outro computador."
            licenca = None
    if licenca is not None:
        quem = licenca["cliente"]
        validade = date.fromisoformat(licenca["validade"]) if licenca.get("validade") else None
        if validade is None:
            return Situacao("licenciado", f"Licenciado · {quem}", f"Licença {licenca['plano']} de {quem}, sem data de vencimento.", None, licenca)
        restantes = (validade - hoje).days
        if restantes >= 0:
            return Situacao(
                "licenciado",
                f"Licenciado · vence {_fmt(validade)}" if restantes <= AVISO_VENCIMENTO_DIAS else f"Licenciado · {quem}",
                f"Licença {licenca['plano']} de {quem}, válida até {_fmt(validade)} ({restantes} dias).",
                restantes,
                licenca,
            )
        return Situacao(
            "licenca_expirada",
            "Licença vencida · somente consulta",
            f"A licença de {quem} venceu em {_fmt(validade)}. O sistema está em modo somente consulta "
            "(você ainda vê e exporta seus dados e faz backup). Renove a licença para voltar a editar.",
            restantes,
            licenca,
        )
    restantes = teste_dias - (hoje - primeiro_uso).days
    if restantes > 0:
        return Situacao(
            "teste",
            f"Teste · {restantes} dia{'s' if restantes != 1 else ''} restante{'s' if restantes != 1 else ''}",
            f"Período de teste gratuito: {restantes} dia{'s' if restantes != 1 else ''} restante{'s' if restantes != 1 else ''}, "
            f"até {_fmt(primeiro_uso + timedelta(days=teste_dias))}.",
            restantes,
            None,
            erro,
        )
    return Situacao(
        "teste_encerrado",
        "Teste encerrado · somente consulta",
        f"O período de teste de {teste_dias} dias terminou. O sistema está em modo somente consulta "
        "(você ainda vê e exporta seus dados e faz backup). Ative uma licença para voltar a editar.",
        0,
        None,
        erro,
    )
