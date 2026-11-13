"""Ferramenta do FORNECEDOR: cria o par de chaves e emite arquivos de licenca (.erplic). Nao vai no app distribuido.

Uso:
  # 1) uma unica vez: cria a chave privada (guarde-a fora do repositorio, com copia segura) e mostra a publica
  python scripts/gerar_licenca.py chaves --saida "C:/Users/voce/ERP_licencas"

  # 2) para cada venda
  python scripts/gerar_licenca.py emitir --chave "C:/Users/voce/ERP_licencas/chave_privada.key" \
      --cliente "Auto Pecas Exemplo" --documento "11.222.333/0001-81" --plano Anual --validade 2027-11-13 \
      --saida "C:/Users/voce/ERP_licencas/emitidas"
  # licenca perpetua: omita --validade. Vinculada a um computador: --maquina XXXX-XXXX-XXXX (codigo mostrado em Sobre)

A chave privada e um arquivo de texto com 64 caracteres hexadecimais. Quem a tiver pode emitir licencas: nunca a
envie, nao a coloque no Git e mantenha uma copia de seguranca (perde-la obriga a trocar a chave publica do app).
"""

from __future__ import annotations

import argparse
import secrets
import sys
from datetime import date
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.services import licenca_service  # noqa: E402
from app.utils import ed25519  # noqa: E402


def _ler_chave(caminho: str) -> bytes:
    try:
        chave = bytes.fromhex(Path(caminho).read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        raise SystemExit(f"Nao foi possivel ler a chave privada em {caminho}.") from None
    if len(chave) != 32:
        raise SystemExit("A chave privada deve ter 64 caracteres hexadecimais (32 bytes).")
    return chave


def comando_chaves(args: argparse.Namespace) -> int:
    pasta = Path(args.saida)
    destino = pasta / "chave_privada.key"
    if destino.exists():
        print(f"Ja existe uma chave em {destino}. Nao vou sobrescrever.")
        return 1
    pasta.mkdir(parents=True, exist_ok=True)
    privada = secrets.token_bytes(32)
    destino.write_text(privada.hex() + "\n", encoding="utf-8")
    publica = ed25519.chave_publica(privada).hex()
    (pasta / "chave_publica.txt").write_text(publica + "\n", encoding="utf-8")
    print(f"Chave privada gravada em: {destino}  (GUARDE E FACA COPIA; nunca envie nem commite)")
    print(f"Chave publica (cole em CHAVE_PUBLICA_HEX de app/services/licenca_service.py):\n{publica}")
    return 0


def comando_emitir(args: argparse.Namespace) -> int:
    chave = _ler_chave(args.chave)
    validade = date.fromisoformat(args.validade) if args.validade else None
    conteudo = licenca_service.montar_licenca(
        chave, args.cliente, args.plano, validade, date.today(), args.documento or "", args.maquina or None
    )
    # confere com a chave publica embutida no app: evita entregar licenca que o app recusaria
    try:
        licenca_service.ler_licenca(conteudo)
    except licenca_service.LicencaInvalida as exc:
        print(f"ERRO: a licenca gerada nao confere com a chave publica embutida no app ({exc}). Chave errada?")
        return 1
    pasta = Path(args.saida)
    pasta.mkdir(parents=True, exist_ok=True)
    nome = "".join(c if c.isalnum() else "_" for c in args.cliente).strip("_") or "cliente"
    destino = pasta / f"licenca_{nome}_{date.today():%Y%m%d}{licenca_service.EXTENSAO}"
    destino.write_text(conteudo, encoding="utf-8")
    print(f"Licenca gerada: {destino}")
    print(f"  cliente: {args.cliente} | plano: {args.plano} | validade: {validade or 'sem vencimento'} | maquina: {args.maquina or 'qualquer'}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Gerador de licencas do ERP Autopecas (uso do fornecedor).")
    sub = parser.add_subparsers(dest="comando", required=True)
    p_chaves = sub.add_parser("chaves", help="cria o par de chaves (uma vez)")
    p_chaves.add_argument("--saida", required=True, help="pasta FORA do repositorio onde gravar a chave privada")
    p_chaves.set_defaults(funcao=comando_chaves)
    p_emitir = sub.add_parser("emitir", help="emite um arquivo de licenca")
    p_emitir.add_argument("--chave", required=True, help="arquivo da chave privada")
    p_emitir.add_argument("--cliente", required=True)
    p_emitir.add_argument("--documento", default="", help="CPF/CNPJ do cliente (opcional)")
    p_emitir.add_argument("--plano", default="Padrao")
    p_emitir.add_argument("--validade", help="AAAA-MM-DD; omita para licenca sem vencimento")
    p_emitir.add_argument("--maquina", help="codigo do computador (Sobre -> Licenca); omita para valer em qualquer um")
    p_emitir.add_argument("--saida", default=str(ROOT_DIR / "licencas_emitidas"), help="pasta de saida")
    p_emitir.set_defaults(funcao=comando_emitir)
    args = parser.parse_args()
    return args.funcao(args)


if __name__ == "__main__":
    sys.exit(main())
