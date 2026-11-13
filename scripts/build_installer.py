"""Gera o instalador Windows (Inno Setup) a partir de dist/ERP_Autopecas (gerado por build_release.py).

Uso:  python scripts/build_installer.py --version 3.2.0
O ISCC.exe e procurado no PATH, na variavel INNO_SETUP (pasta) e nas pastas padrao do Inno Setup 6.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPT = ROOT_DIR / "installer" / "ERP_Autopecas.iss"
RELEASES_DIR = ROOT_DIR / "releases"


def localizar_iscc() -> Path | None:
    achado = shutil.which("ISCC") or shutil.which("ISCC.exe")
    if achado:
        return Path(achado)
    candidatos = []
    if os.environ.get("INNO_SETUP"):
        candidatos.append(Path(os.environ["INNO_SETUP"]) / "ISCC.exe")
    for base in (os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles"), os.environ.get("LOCALAPPDATA")):
        if base:
            candidatos.append(Path(base) / "Inno Setup 6" / "ISCC.exe")
            candidatos.append(Path(base) / "Programs" / "Inno Setup 6" / "ISCC.exe")
    return next((c for c in candidatos if c.is_file()), None)


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera o instalador do ERP Autopecas (Inno Setup).")
    parser.add_argument("--version", required=True, help="Versao exibida no instalador (ex.: 3.2.0).")
    args = parser.parse_args()

    if not (ROOT_DIR / "dist" / "ERP_Autopecas" / "ERP_Autopecas.exe").is_file():
        print("dist/ERP_Autopecas/ERP_Autopecas.exe nao encontrado. Rode antes: python scripts/build_release.py --version <v>")
        return 1
    iscc = localizar_iscc()
    if iscc is None:
        print("ISCC.exe (Inno Setup 6) nao encontrado. Instale em https://jrsoftware.org/isinfo.php ou defina INNO_SETUP.")
        return 1
    RELEASES_DIR.mkdir(parents=True, exist_ok=True)
    comando = [str(iscc), f"/DAppVersion={args.version}", f"/O{RELEASES_DIR}", str(SCRIPT)]
    if subprocess.run(comando, cwd=ROOT_DIR, check=False).returncode != 0:
        print("Falha ao compilar o instalador.")
        return 1
    print(f"Instalador gerado: {RELEASES_DIR / f'ERP_Autopecas_Setup_{args.version}.exe'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
