from __future__ import annotations

import sys
from pathlib import Path
from zipfile import ZipFile

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.controllers.relatorio_controller import RelatorioController
from app.controllers.seguranca_controller import SegurancaController
from app.database.init_db import initialize_database
from app.utils.sessao import Sessao


def main() -> int:
    initialize_database()
    Sessao.iniciar_sistema()  # script sem usuario interativo
    relatorio = RelatorioController()
    pdf = relatorio.gerar("financeiro", "pdf")
    xlsx = relatorio.gerar("estoque", "xlsx")
    if not Path(pdf).exists() or not Path(pdf).read_bytes().startswith(b"%PDF"):
        raise RuntimeError("Falha ao validar relatorio PDF.")
    with ZipFile(xlsx) as arquivo_xlsx:
        if "xl/workbook.xml" not in arquivo_xlsx.namelist():
            raise RuntimeError("Falha ao validar relatorio XLSX.")

    backup = SegurancaController().criar_backup(usuario_id=None)
    if not Path(backup).exists():
        raise RuntimeError("Falha ao validar backup.")

    print("Homologacao smoke OK")
    print(f"PDF: {pdf}")
    print(f"XLSX: {xlsx}")
    print(f"Backup: {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
